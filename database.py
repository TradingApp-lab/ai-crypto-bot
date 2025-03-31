import sqlalchemy as sa

engine = sa.create_engine("sqlite:///historical_data.db")

metadata = sa.MetaData()

ohlcv_table = sa.Table(
    'ohlcv', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('symbol', sa.String),
    sa.Column('timestamp', sa.Integer, unique=True),
    sa.Column('open', sa.Float),
    sa.Column('high', sa.Float),
    sa.Column('low', sa.Float),
    sa.Column('close', sa.Float),
    sa.Column('volume', sa.Float)
)

metadata.create_all(engine)
