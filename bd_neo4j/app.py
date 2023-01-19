import os
from typing import Dict

from flask import Flask, jsonify, request
from neo4j import GraphDatabase, ManagedTransaction
from dotenv import load_dotenv

load_dotenv("./config.env")

app = Flask(__name__)

uri = os.getenv("URI")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(username, password), database="neo4j")


# ---- EMPLOYEES ----
# Get employees
def get_employees(tx: ManagedTransaction, data: Dict[str, any]):
    query = ""
    wherePart = []

    if "lastName" in data:
        query = (
            f"CALL db.index.fulltext.queryNodes('lastNameIndex', $lastName)\n"
            "YIELD node, score"
        )
    else:
        query = "MATCH (node:Employee)"

    if "department" in data:
        query += " MATCH (node)-[:WORKS_IN]->(d:Department {name: $department})"

    for field in ("firstName", "lastName"):
        if field not in data:
            continue

        wherePart.append([field, data[field]])

    if wherePart:
        query += "WHERE " + " AND ".join(wherePart)

    query += "RETURN node"
    print(query)
    # results = tx.run(query).data()
    # employees = [
    #     {
    #         "employee": {
    #             "firstName": result["node"].get("firstName"),
    #             "lastName": result["node"].get("lastName"),
    #         },
    #         "score": result["score"],
    #     }
    #     for result in results
    # ]
    # return employees


# Add employees
def add_employee(tx: ManagedTransaction, data: Dict[str, any]):
    query = "CREATE (n:Employee {firstName: $firstName, lastName: $lastName})"
    summary = tx.run(query, **data).consume()
    print(summary.profile)


# Routes
@app.route("/employees", methods=["GET", "POST"])
def employees_route():
    if request.method == "GET":
        with driver.session() as session:
            employees = session.execute_read(
                get_employees, request.args.get("lastName")
            )

        response = {"employees": employees}
        return jsonify(response)
    else:
        print(request.json)
        with driver.session() as session:
            session.execute_write(add_employee, request.json)

        return jsonify({"status": "created"})


# ---- DEPARTMENTS ----


if __name__ == "__main__":
    # Setup the search index
    with driver.session() as session:
        session.run(
            (
                "CREATE FULLTEXT INDEX lastNameIndex IF NOT EXISTS\n"
                "FOR (n:Employee)\n"
                "ON EACH [ n.lastName ]"
            )
        )

    app.run()
