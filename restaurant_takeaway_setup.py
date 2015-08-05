import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Restaurant(Base):
    __tablename__ = 'restaurant'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    address = Column(String(300))

# We added this serialize function to be able to send JSON objects in a
# serializable format
    @property
    def serialize(self):
        #Returns object data in easily serializable format
        return {
            'name':self.name,
            'id':self.id,
            'address':self.address
        }

class MenuItem(Base):
    __tablename__ = 'menuitem'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    price = Column(Float)
    course = Column(String(250))
    
    restaurant = relationship(Restaurant)
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))

# We added this serialize function to be able to send JSON objects in a
# serializable format
    @property
    def serialize(self):
        #Returns object data in easily serializable format
        return {
            'name':self.name,
            'id':self.id,
            'description':self.description,
            'price':self.price,
            'restaurant_id':self.restaurant_id,
        }


class Customer(Base):
    __tablename__ = 'customer'

    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    password=Column(String(250), nullable=False)
    email=Column(String(250))
    phone_number=Column(Integer)
    first_name=Column(String(250))
    surname=Column(String(250))
    preferred_billing_address=Column(String(300))
    preferred_delivery_address=Column(String(300))

# We added this serialize function to be able to send JSON objects in a
# serializable format
    @property
    def serialize(self):
        #Returns object data in easily serializable format
        return {
            'username':self.username,
            'id':self.id,
            'email':self.email,
            'phone_number':self.phone_number,
            'first_name':self.first_name,
            'surname':self.surname,
            'preferred_billing_address':self.preferred_billing_address,
            'preferred_delivery_address':self.preferred_delivery_address
        }
        
class CustomerOrder(Base):
    __tablename__ = 'customerorder'

    id = Column(Integer, primary_key=True)
    
    customer_id = Column(Integer,ForeignKey('customer.id'))
    customer_id_relationship = relationship("Customer", foreign_keys="CustomerOrder.customer_id")
    
    customer_username = Column(String(250),ForeignKey('customer.username'))
    customer_username_relationship = relationship("Customer", foreign_keys="CustomerOrder.customer_username")
    
    restaurant = relationship(Restaurant)
    restaurant_id = Column(Integer,ForeignKey('restaurant.id'))
    
    total_price = Column(Float)
    place_order_time = Column(DateTime, nullable=False)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    completion_status = Column(Boolean)

    customer_phone_number=Column(Integer)
    customer_billing_address=Column(String(300))
    customer_delivery_address=Column(String(300))

    customerorderhash = Column(String(250))

# We added this serialize function to be able to send JSON objects in a
# serializable format
    @property
    def serialize(self):
        #Returns object data in easily serializable format
        return {
            'id':self.id,
            'customer_id':self.customer_id,
            'customer_username':self.customer_username,
            'restaurant_id':self.restaurant_id,
            'total_price':self.total_price,
            'place_order_time':self.place_order_time,
            'departure_time':self.departure_time,
            'arrival_time':self.arrival_time,
            'completion_status':self.completion_status,
            'customerorderhash':self.customerorderhash,
            'customer_phone_number':self.customer_phone_number,
            'customer_billing_address':self.customer_billing_address,
            'customer_delivery_address':self.customer_delivery_address
        }

class Staff(Base):
    __tablename__ = 'staff'

    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    password = Column(String(250), nullable=False)
    email = Column(String(250))
        
    restaurant = relationship(Restaurant)
    restaurant_id = Column(Integer,ForeignKey('restaurant.id'))

# We added this serialize function to be able to send JSON objects in a
# serializable format
    @property
    def serialize(self):
        #Returns object data in easily serializable format
        return {
            'username':self.username,
            'id':self.id,
            'email':self.email,
            'restaurant_id':self.restaurant_id
        }

class CustomerOrderedItem(Base):
    __tablename__ = 'customerordereditem'
    
    id = Column(Integer, primary_key=True)
    
    restaurant = relationship(Restaurant)
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    
    customer = relationship(Customer)
    customer_id = Column(Integer, ForeignKey('customer.id'))
    
    customerorder = relationship(CustomerOrder)
    customerorder_id = Column(Integer, ForeignKey('customerorder.id'))
    
    menuitem = relationship(MenuItem)
    menuitem_id = Column(Integer, ForeignKey('menuitem.id'))

    menuitem_price = Column(Float)
    
# We added this serialize function to be able to send JSON objects in a
# serializable format
    @property
    def serialize(self):
        #Returns object data in easily serializable format
        return {
            'restaurant_id':self.restaurant_id,
            'customer_id':self.customer_id,
            'customerorder_id':self.customerorder_id,
            'menuitem_id':self.menuitem_id,
            'menuitem_price':self.menuitem_price
        }

engine = create_engine('sqlite:///restaurant_takeaway_system.db')

Base.metadata.create_all(engine)
