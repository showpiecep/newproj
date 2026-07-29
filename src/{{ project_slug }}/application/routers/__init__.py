"""HTTP routers exposed by the application.

Place FastAPI routers in separate modules grouped by API responsibility. Import and
register them in the application assembly layer; routers should delegate business
operations to use cases instead of containing business logic.
"""
