from py2neo import Graph, Node, Relationship #, authenticate #depreciated in v4
import uuid
from datetime import datetime
#from json import dumps
import json
from flask import session
import os

# set up authentication parameters
#authenticate("localhost:7474", "neo4j", "neo4j")
#graph = Graph("http://localhost:7474/db/data/")

#authenticate("127.0.0.1:7474", "neo4j", "neo4j") #Local neo4j
#graph = Graph("http://127.0.0.1:7474/db/data/") #Local neo4j

#Access to Google Compute Engine hosting neo4j
graph = Graph("bolt://34.83.30.187:7687", auth=("neo4j","rx2u-neo4j"), bolt=True, secure = True, http_port = 24789, https_port = 24780)

class User:
    def placeorder(userinfo):
        id=str(uuid.uuid4())
        orderNum=id[-6:]

        user = Node(
            "User",
            id=str(uuid.uuid4()),
            first=userinfo["first"],
            last=userinfo["last"],
            phone=userinfo["phone"],
            dob=userinfo["dob"],
            address=userinfo["address"],
            pharmacy=userinfo["pharmacy"],
            rx=userinfo["rx"]
        )

        order = Node(
            "Order",
            id=str(uuid.uuid4()),
            orderNum=orderNum,
            status="New",
            message="With Pharmacy",
            date=datetime.now().strftime('%m-%d-%Y')
        )

        rel = Relationship(user, "PLACED", order)

        graph.create(user)
        graph.create(order)
        graph.create(rel)

        return orderNum

    def placeUserOrder(username):
        id=str(uuid.uuid4())
        orderNum=id[-6:]

        userinfo = list(User.populateUserInfo(username))

        user = Node(
            "User",
            id=str(uuid.uuid4()),
            first=userinfo[0][0]["first"],
            last=userinfo[0][0]["last"],
            phone=userinfo[0][0]["phone"],
            dob=userinfo[0][0]["dob"],
            address=userinfo[0][0]["address"],
            pharmacy=userinfo[0][0]["pharmacy"],
            rx=userinfo[0][0]["rx"],
            username=userinfo[0][0]["username"],
            password=userinfo[0][0]["password"]
        )

        order = Node(
            "Order",
            id=str(uuid.uuid4()),
            orderNum=orderNum,
            status="New",
            message="With Pharmacy",
            date=datetime.now().strftime('%m-%d-%Y')
        )

        rel = Relationship(user, "PLACED", order)

        graph.create(user)
        graph.create(order)
        graph.create(rel)

        return orderNum

    def timestamp():
        epoch = datetime.utcfromtimestamp(0)
        now = datetime.now()
        delta = now - epoch
        return delta.total_seconds()

    def checkOrderStatus():
        query = """
        MATCH (user:User)-[:PLACED]->(order:Order)
        OPTIONAL MATCH (user:User)-[:PLACED]->(order:Order)<-[:FILLED]-(pharmacy:Pharmacy)
        OPTIONAL MATCH (user:User)-[:PLACED]->(order:Order)<-[:COMPLETED]-(pharmacy:Pharmacy)
        OPTIONAL MATCH (user:User)-[:PLACED]->(order:Order)<-[:PICKEDUP]-(uber:Uber)
        OPTIONAL MATCH (user:User)-[:PLACED]->(order:Order)<-[:DELIVERED]-(uber:Uber)
        OPTIONAL MATCH (user:User)-[:RECEIVED]->(order:Order)<-[:DELIVERED]-(uber:Uber)
        RETURN order.orderNum as orderNum, order.status as status, order.message as message
        """
        return graph.run(query)

    def lookupOrder(orderNum):
        query = """
        MATCH (user:User)-[:PLACED]->(order:Order{orderNum:{orderNum}})
        OPTIONAL MATCH (user:User)-[:PLACED]->(order:Order)<-[:FILLED]-(pharmacy:Pharmacy)
        OPTIONAL MATCH (user:User)-[:PLACED]->(order:Order)<-[:COMPLETED]-(pharmacy:Pharmacy)
        OPTIONAL MATCH (user:User)-[:PLACED]->(order:Order)<-[:PICKEDUP]-(uber:Uber)
        OPTIONAL MATCH (user:User)-[:PLACED]->(order:Order)<-[:DELIVERED]-(uber:Uber)
        OPTIONAL MATCH (user:User)-[:RECEIVED]->(order:Order)<-[:DELIVERED]-(uber:Uber)
        RETURN order.orderNum as orderNum, order.status as status, order.message as message
        """
        return graph.run(query, orderNum=orderNum)

    def populateOrders():
        query = """
        MATCH (user:User)-[:PLACED]->(order:Order)
        RETURN user, order
        """
        return graph.run(query)

    def populateUserOrders(username):
        query = """
        MATCH (user:User)-[:PLACED]->(order:Order)
        WHERE user.username={username}
        RETURN user, order
        """
        return graph.run(query, username=username)

    def populateUserInfo(username):
        query = """
        MATCH (user:User)
        WHERE user.username={username}
        RETURN user limit 1
        """
        return graph.run(query, username=username)

    def receiveOrder(orderNum, phone):
        query = """
        MATCH (order:Order), (user:User)
        WHERE order.orderNum ={orderNum} and user.phone={phone}
        SET order.status = 'Delivered'
        SET order.message = 'Package delivered'
        CREATE (user)-[:RECEIVED]->(order)
        """
        return graph.run(query, orderNum=orderNum, phone=phone)

    def find(username):
        #depreciated in py2neo v4
        #user = graph.find_one("User", "username", username)
        user = graph.nodes.match("User", username=username).first()
        return user

    def register(userinfo):
        user = Node(
            "User",
            id=str(uuid.uuid4()),
            username=userinfo["username"],
            password=userinfo["password"],
            first=userinfo["first"],
            last=userinfo["last"],
            phone=userinfo["phone"],
            dob=userinfo["dob"],
            address=userinfo["address"],
            pharmacy=userinfo["pharmacy"]
        )
        graph.create(user)

    def verifyPassword(username, password):
        query = """
        MATCH (user:User)
        WHERE user.username={username} and user.password={password}
        RETURN user.username as username limit 1
        """
        return graph.run(query, username=username, password=password)

class Pharmacy:
    def populateOrders():
        query = """
        MATCH (user:User)-[:PLACED]->(order:Order)
        RETURN user, order
        """
        return graph.run(query)

    def completeOrder(orderNum):
        pharmacy = Node(
            "Pharmacy",
            name="Pharmacy1"
        )
        graph.create(pharmacy)

        query = """
        MATCH (order:Order), (pharmacy:Pharmacy)
        WHERE order.orderNum ={orderNum} and pharmacy.name='Pharmacy1'
        SET order.status = 'Ready'
        SET order.message = 'Requesting Uber'
        CREATE (pharmacy)-[:COMPLETED]->(order)
        """
        return graph.run(query, orderNum=orderNum)

    def register(userinfo):
        user = Node(
            "User",
            id=str(uuid.uuid4()),
            first=userinfo["first"],
            last=userinfo["last"],
            phone=userinfo["phone"],
            dob=userinfo["dob"],
            address=userinfo["address"],
            pharmacy=userinfo["pharmacy"],
            rx=userinfo["rx"]
        )
        graph.create(user)

class Uber:
    def populateOrders():
        query = """
        MATCH (user:User)-[:PLACED]->(order:Order)
        RETURN user, order
        """
        return graph.run(query)

    def startOrder(orderNum):
        uber = Node(
            "Uber",
            name="Uber1",
            rate="****"
        )
        graph.create(uber)

        query = """
        MATCH (order:Order), (uber:Uber)
        WHERE order.orderNum ={orderNum} and uber.name='Uber1'
        SET order.status = 'Enrouted'
        SET order.message = 'Uber Ride starts'
        CREATE (uber)-[:STARTED]->(order)
        """
        return graph.run(query, orderNum=orderNum)

    def endOrder(orderNum):
        query = """
        MATCH (order:Order), (uber:Uber)
        WHERE order.orderNum ={orderNum} and uber.name='Uber1'
        SET order.status = 'Arrived'
        SET order.message = 'Arrived at destination'
        CREATE (uber)-[:ENDED]->(order)
        """
        return graph.run(query, orderNum=orderNum)
