class Restaurant:
    def __init__(self, name, menu):
        self.name = name
        self.menu = menu

    def get_menu(self):
        return dict(self.menu)

    def is_item_available(self, item_name):
        if item_name not in self.menu:
            raise ValueError(f"Item '{item_name}' not found in menu")
        return self.menu[item_name]["available"]

    def get_item_price(self, item_name):
        if item_name not in self.menu:
            raise ValueError(f"Item '{item_name}' not found in menu")
        return self.menu[item_name]["price"]


class RestaurantBrowser:
    def __init__(self):
        self.restaurants = []

    def add_restaurant(self, restaurant):
        self.restaurants.append(restaurant)

    def browse(self):
        return [r.name for r in self.restaurants]

    def find_restaurant(self, name):
        for r in self.restaurants:
            if r.name == name:
                return r
        raise ValueError(f"Restaurant '{name}' not found")
