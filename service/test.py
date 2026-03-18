from service.api import get_categories
from service.api import get_subcategories
from service.api import get_words

print(get_categories())
print( get_subcategories("Academic English"))
print(get_words("Academic English","Presentation"))