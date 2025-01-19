from loader import dp
from .is_owner import IsOwner, IsOwnerCall

if __name__ == "filters":
    dp.filters_factory.bind(IsOwner)
    dp.filters_factory.bind(IsOwnerCall)
    pass
