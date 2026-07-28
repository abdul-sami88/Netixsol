# Part 1: Relationship Discovery

## Primary Keys

- actor: actor_id
- film: film_id
- category: category_id
- customer: customer_id
- address: address_id
- city: city_id
- country: country_id
- inventory: inventory_id
- rental: rental_id
- payment: payment_id
- staff: staff_id
- store: store_id

## Foreign Keys

- film_actor: actor_id (ref: actor), film_id (ref: film)
- film_category: film_id (ref: film), category_id (ref: category)
- address: city_id (ref: city)
- city: country_id (ref: country)
- customer: store_id (ref: store), address_id (ref: address)
- inventory: film_id (ref: film), store_id (ref: store)
- rental: inventory_id (ref: inventory), customer_id (ref: customer), staff_id (ref: staff)
- payment: customer_id (ref: customer), staff_id (ref: staff), rental_id (ref: rental)
- store: manager_staff_id (ref: staff), address_id (ref: address)

## Relationship Diagram

![ERD_Diagram](Screenshots/ERD_diagram.png)
