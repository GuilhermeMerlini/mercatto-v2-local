"""This file imports all models.py from each module to register SQLModel tables."""

from app.modules.users.models import *
from app.modules.catalog.models import *
from app.modules.search.models import *
from app.modules.cart.models import *
from app.modules.orders.models import *
from app.modules.payments.models import *
from app.modules.reviews.models import *
from app.modules.sellers.models import *
