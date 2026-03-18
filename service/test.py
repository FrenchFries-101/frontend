from service.api import get_categories
from service.api import get_subcategories
from service.api import get_words
from service.api_forum import get_posts

data = get_posts()
print(data)
# print(get_categories())
# print( get_subcategories("Academic English"))
# print(get_words("Academic English","Presentation"))