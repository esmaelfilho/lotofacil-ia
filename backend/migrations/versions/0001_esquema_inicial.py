"""Esquema inicial: função de validação das dezenas e todas as tabelas da versão 1.

O autogenerate do Alembic não detecta funções SQL; por isso a função
lotofacil_dezenas_validas é criada e removida manualmente com op.execute().

Revisão: 0001
Anterior: (nenhuma)
Criada em: 2026-10-12 14:21:26.037918+00:00
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Válido quando: uma dimensão (ou vazio), sem NULL, valores de 1 a 25, sem repetição,
# em ordem estritamente crescente e com quantidade entre qtd_min e qtd_max.
CRIAR_FUNCAO_DEZENAS = """
CREATE FUNCTION lotofacil_dezenas_validas(d smallint[], qtd_min int, qtd_max int)
RETURNS boolean
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
AS $$
    SELECT (cardinality(d) = 0 OR array_ndims(d) = 1)
       AND cardinality(d) BETWEEN qtd_min AND qtd_max
       AND d = ARRAY(SELECT DISTINCT x FROM unnest(d) AS x
                     WHERE x BETWEEN 1 AND 25 ORDER BY x)
$$
"""


def upgrade() -> None:
    op.execute(CRIAR_FUNCAO_DEZENAS)
    op.create_table('estrategias',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('nome', sa.String(length=120), nullable=False),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('ativa', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('criada_em', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('atualizada_em', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_estrategias')),
    sa.UniqueConstraint('nome', name=op.f('uq_estrategias_nome'))
    )
    op.create_table('historico_importacoes',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('origem', sa.String(length=20), nullable=False),
    sa.Column('referencia', sa.String(length=255), nullable=False),
    sa.Column('hash_conteudo', sa.String(length=64), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='EM_ANDAMENTO', nullable=False),
    sa.Column('total_lidos', sa.Integer(), server_default='0', nullable=False),
    sa.Column('total_inseridos', sa.Integer(), server_default='0', nullable=False),
    sa.Column('total_ignorados', sa.Integer(), server_default='0', nullable=False),
    sa.Column('total_rejeitados', sa.Integer(), server_default='0', nullable=False),
    sa.Column('mensagem_erro', sa.Text(), nullable=True),
    sa.Column('iniciada_em', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finalizada_em', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.CheckConstraint("origem IN ('ARQUIVO', 'API')", name=op.f('ck_historico_importacoes_origem')),
    sa.CheckConstraint("status IN ('EM_ANDAMENTO', 'CONCLUIDA', 'CONCLUIDA_COM_REJEICOES', 'FALHOU')", name=op.f('ck_historico_importacoes_status')),
    sa.CheckConstraint('finalizada_em IS NULL OR finalizada_em >= iniciada_em', name=op.f('ck_historico_importacoes_periodo')),
    sa.CheckConstraint('total_lidos >= 0 AND total_inseridos >= 0 AND total_ignorados >= 0 AND total_rejeitados >= 0', name=op.f('ck_historico_importacoes_totais_nao_negativos')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_historico_importacoes'))
    )
    op.create_table('regras_estatisticas',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('codigo', sa.String(length=50), nullable=False),
    sa.Column('nome', sa.String(length=120), nullable=False),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('parametros_padrao', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('ativa', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.CheckConstraint("jsonb_typeof(parametros_padrao) = 'object'", name=op.f('ck_regras_estatisticas_parametros_objeto')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_regras_estatisticas')),
    sa.UniqueConstraint('codigo', name=op.f('uq_regras_estatisticas_codigo'))
    )
    op.create_table('concursos',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('numero', sa.Integer(), nullable=False),
    sa.Column('data_sorteio', sa.Date(), nullable=False),
    sa.Column('dezenas', postgresql.ARRAY(sa.SmallInteger(), dimensions=1), nullable=False),
    sa.Column('importacao_id', sa.BigInteger(), nullable=True),
    sa.Column('criado_em', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('lotofacil_dezenas_validas(dezenas, 15, 15)', name=op.f('ck_concursos_dezenas')),
    sa.CheckConstraint('numero > 0', name=op.f('ck_concursos_numero_positivo')),
    sa.ForeignKeyConstraint(['importacao_id'], ['historico_importacoes.id'], name=op.f('fk_concursos_importacao_id_historico_importacoes'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_concursos')),
    sa.UniqueConstraint('numero', name=op.f('uq_concursos_numero'))
    )
    op.create_index(op.f('ix_concursos_data_sorteio'), 'concursos', ['data_sorteio'], unique=False)
    op.create_index(op.f('ix_concursos_importacao_id'), 'concursos', ['importacao_id'], unique=False)
    op.create_table('estrategia_regras',
    sa.Column('estrategia_id', sa.BigInteger(), nullable=False),
    sa.Column('regra_id', sa.BigInteger(), nullable=False),
    sa.Column('parametros', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.CheckConstraint("jsonb_typeof(parametros) = 'object'", name=op.f('ck_estrategia_regras_parametros_objeto')),
    sa.ForeignKeyConstraint(['estrategia_id'], ['estrategias.id'], name=op.f('fk_estrategia_regras_estrategia_id_estrategias'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['regra_id'], ['regras_estatisticas.id'], name=op.f('fk_estrategia_regras_regra_id_regras_estatisticas'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('estrategia_id', 'regra_id', name=op.f('pk_estrategia_regras'))
    )
    op.create_index(op.f('ix_estrategia_regras_regra_id'), 'estrategia_regras', ['regra_id'], unique=False)
    op.create_table('geracoes_jogos',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('estrategia_id', sa.BigInteger(), nullable=True),
    sa.Column('concurso_base_numero', sa.Integer(), nullable=False),
    sa.Column('quantidade_jogos', sa.Integer(), nullable=False),
    sa.Column('dezenas_por_jogo', sa.SmallInteger(), server_default='15', nullable=False),
    sa.Column('dezenas_obrigatorias', postgresql.ARRAY(sa.SmallInteger(), dimensions=1), server_default=sa.text("'{}'::smallint[]"), nullable=False),
    sa.Column('dezenas_excluidas', postgresql.ARRAY(sa.SmallInteger(), dimensions=1), server_default=sa.text("'{}'::smallint[]"), nullable=False),
    sa.Column('parametros', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('semente', sa.BigInteger(), nullable=True),
    sa.Column('criada_em', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("jsonb_typeof(parametros) = 'object'", name=op.f('ck_geracoes_jogos_parametros_objeto')),
    sa.CheckConstraint('25 - cardinality(dezenas_excluidas) >= dezenas_por_jogo', name=op.f('ck_geracoes_jogos_excluidas_permitem_jogo')),
    sa.CheckConstraint('NOT (dezenas_obrigatorias && dezenas_excluidas)', name=op.f('ck_geracoes_jogos_obrigatorias_excluidas_disjuntas')),
    sa.CheckConstraint('cardinality(dezenas_obrigatorias) <= dezenas_por_jogo', name=op.f('ck_geracoes_jogos_obrigatorias_cabem')),
    sa.CheckConstraint('dezenas_por_jogo BETWEEN 15 AND 20', name=op.f('ck_geracoes_jogos_dezenas_por_jogo')),
    sa.CheckConstraint('lotofacil_dezenas_validas(dezenas_excluidas, 0, 10)', name=op.f('ck_geracoes_jogos_excluidas')),
    sa.CheckConstraint('lotofacil_dezenas_validas(dezenas_obrigatorias, 0, 20)', name=op.f('ck_geracoes_jogos_obrigatorias')),
    sa.CheckConstraint('quantidade_jogos > 0', name=op.f('ck_geracoes_jogos_quantidade_positiva')),
    sa.ForeignKeyConstraint(['concurso_base_numero'], ['concursos.numero'], name=op.f('fk_geracoes_jogos_concurso_base_numero_concursos'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['estrategia_id'], ['estrategias.id'], name=op.f('fk_geracoes_jogos_estrategia_id_estrategias'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_geracoes_jogos'))
    )
    op.create_index(op.f('ix_geracoes_jogos_concurso_base_numero'), 'geracoes_jogos', ['concurso_base_numero'], unique=False)
    op.create_index(op.f('ix_geracoes_jogos_estrategia_id'), 'geracoes_jogos', ['estrategia_id'], unique=False)
    op.create_table('jogos_gerados',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('geracao_id', sa.BigInteger(), nullable=False),
    sa.Column('sequencia', sa.Integer(), nullable=False),
    sa.Column('dezenas', postgresql.ARRAY(sa.SmallInteger(), dimensions=1), nullable=False),
    sa.CheckConstraint('lotofacil_dezenas_validas(dezenas, 15, 20)', name=op.f('ck_jogos_gerados_dezenas')),
    sa.CheckConstraint('sequencia > 0', name=op.f('ck_jogos_gerados_sequencia_positiva')),
    sa.ForeignKeyConstraint(['geracao_id'], ['geracoes_jogos.id'], name=op.f('fk_jogos_gerados_geracao_id_geracoes_jogos'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_jogos_gerados')),
    sa.UniqueConstraint('geracao_id', 'dezenas', name=op.f('uq_jogos_gerados_geracao_id_dezenas')),
    sa.UniqueConstraint('geracao_id', 'sequencia', name=op.f('uq_jogos_gerados_geracao_id_sequencia'))
    )
    op.create_table('avaliacoes',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('jogo_id', sa.BigInteger(), nullable=False),
    sa.Column('concurso_id', sa.BigInteger(), nullable=False),
    sa.Column('acertos', sa.SmallInteger(), nullable=False),
    sa.Column('avaliada_em', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('acertos BETWEEN 0 AND 15', name=op.f('ck_avaliacoes_acertos')),
    sa.ForeignKeyConstraint(['concurso_id'], ['concursos.id'], name=op.f('fk_avaliacoes_concurso_id_concursos'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['jogo_id'], ['jogos_gerados.id'], name=op.f('fk_avaliacoes_jogo_id_jogos_gerados'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_avaliacoes')),
    sa.UniqueConstraint('jogo_id', 'concurso_id', name=op.f('uq_avaliacoes_jogo_id_concurso_id'))
    )
    op.create_index(op.f('ix_avaliacoes_concurso_id'), 'avaliacoes', ['concurso_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_avaliacoes_concurso_id'), table_name='avaliacoes')
    op.drop_table('avaliacoes')
    op.drop_table('jogos_gerados')
    op.drop_index(op.f('ix_geracoes_jogos_estrategia_id'), table_name='geracoes_jogos')
    op.drop_index(op.f('ix_geracoes_jogos_concurso_base_numero'), table_name='geracoes_jogos')
    op.drop_table('geracoes_jogos')
    op.drop_index(op.f('ix_estrategia_regras_regra_id'), table_name='estrategia_regras')
    op.drop_table('estrategia_regras')
    op.drop_index(op.f('ix_concursos_importacao_id'), table_name='concursos')
    op.drop_index(op.f('ix_concursos_data_sorteio'), table_name='concursos')
    op.drop_table('concursos')
    op.drop_table('regras_estatisticas')
    op.drop_table('historico_importacoes')
    op.drop_table('estrategias')
    op.execute("DROP FUNCTION lotofacil_dezenas_validas(smallint[], int, int)")
