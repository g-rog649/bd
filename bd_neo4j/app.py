import os
import itertools
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
def prepare_get_employee_query_string(entries):
    where_list = []
    order_by_list = []
    where_str = ""
    order_by_str = ""
    match_str = "MATCH (n:Employee)-[:WORKS_IN]->(d:Department)"

    # Make where_list and order_by_list
    for field, value in entries.items():
        search_term, order, *_ = value.split(",") + [""]
        node_name = "d" if field == "department" else "n"

        if search_term:
            where_list.append(
                (node_name, field if node_name == "n" else "name", search_term)
            )

        if order in ("asc", "desc"):
            order_by_list.append(
                (node_name, field if node_name == "n" else "name", order.upper())
            )

    # WHERE ...
    if where_list:
        where_str = "\nWHERE " + " AND ".join(
            f'{node_name}.{field} = "{search_term}"'
            for node_name, field, search_term in where_list
        )

    # ORDER BY ...
    if order_by_list:
        order_by_str = "\nORDER BY " + ", ".join(
            f"{node_name}.{field} {order}" for node_name, field, order in order_by_list
        )

    full_str = match_str + where_str + "\nRETURN n, d" + order_by_str
    return full_str


def get_employees(query: str):
    def get_employees_return(tx: ManagedTransaction):
        # print(query)
        results = tx.run(query).data()
        employees = [
            {
                "firstName": result["n"].get("firstName"),
                "lastName": result["n"].get("lastName"),
                "department": result["d"].get("name"),
            }
            for result in results
        ]

        employees_group = []
        for key, group in itertools.groupby(
            employees, key=lambda k: (k["firstName"], k["lastName"])
        ):
            first_name, last_name = key
            employees_group.append(
                {
                    "firstName": first_name,
                    "lastName": last_name,
                    "department": [d["department"] for d in group],
                }
            )

        print(employees_group)
        return employees

    return get_employees_return


# Add employees
def add_employee(tx: ManagedTransaction, data: Dict[str, any]):
    query = "CREATE (n:Employee {firstName: $firstName, lastName: $lastName})"
    summary = tx.run(query, **data).consume()
    print(summary.profile)


# Update employees
def update_employee_transaction(first_name: str, last_name: str, data: dict):
    set_list = []
    set_str = ""
    allowed_keys = {"firstName", "lastName"}

    for key, value in data.items():
        if key in allowed_keys:
            set_list.append((key, value))

    if set_list:
        set_str = "\nSET " + ", ".join(
            f'n.{key} = "{value}"' for key, value in set_list
        )

    query = "MATCH (n:Employee {firstName: $firstName, lastName: $lastName})" + set_str

    print(query)

    def update_employee(tx: ManagedTransaction):
        summary = tx.run(
            query, {"firstName": first_name, "lastName": last_name}
        ).consume()
        print(summary.profile)

    return update_employee


def transpose(l: list):
    return list(map(list, zip(*l)))


# Routes
@app.route("/employees", methods=["GET", "POST"])
def employees_route():
    if request.method == "GET":
        with driver.session() as session:
            query = prepare_get_employee_query_string(request.args)
            employees = session.execute_read(get_employees(query))

        return jsonify({})
    else:
        print(request.json)
        with driver.session() as session:
            session.execute_write(add_employee, request.json)

        return jsonify({"status": "created"})


@app.route("/employees/<id>", methods=["PUT", "DELETE"])
def employees_id_route(id):
    id_split = id.split("_")
    if len(id_split) != 2:
        return jsonify({"error": "bad user id"})

    first_name, last_name = id_split

    if request.method == "PUT":
        with driver.session() as session:
            update_employee = update_employee_transaction(
                first_name, last_name, request.json
            )
            session.execute_write(update_employee)

        return jsonify({})
    elif request.method == "DELETE":
        pass
    # with driver.session() as session:
    #     session.execute_write


# ---- DEPARTMENTS ----
# Get departments
def prepare_get_department_query_string(entries):
    where_list = []
    order_by_list = []
    where_str = ""
    order_by_str = ""
    match_str = (
        "MATCH (n:Employee)-[r:WORKS_IN]->(d:Department)\n"
        "WITH d, count(r) as employeeCount"
    )

    # Make where_list and order_by_list
    for field, value in entries.items():
        search_term, order, *_ = value.split(",") + [""]
        node_name = "d" if field == "department" else "employeeCount"

        if field == "department":
            first_part = "d.name"
        elif field == "employeeCount":
            first_part = "employeeCount"

        if first_part:
            if search_term:
                where_list.append((first_part, int(search_term)))

            if order in ("asc", "desc"):
                order_by_list.append((first_part, order.upper()))

    # WHERE ...
    if where_list:
        where_str = "\nWHERE " + " AND ".join(
            f"{first_part} = {repr(search_term)}"
            for first_part, search_term in where_list
        )

    # ORDER BY ...
    if order_by_list:
        order_by_str = "\nORDER BY " + ", ".join(
            f"{first_part} {order}" for first_part, order in order_by_list
        )

    full_str = match_str + where_str + "\nRETURN d, employeeCount" + order_by_str
    return full_str


def get_departments(query: str):
    def get_departments_return(tx: ManagedTransaction):
        results = tx.run(query).data()
        departments = [
            {
                "department": result["d"].get("name"),
                "employeeCount": result["employeeCount"],
            }
            for result in results
        ]

        return departments

    return get_departments_return


@app.route("/departments", methods=["GET"])
def departments_route():
    with driver.session() as session:
        query = prepare_get_department_query_string(request.args)
        print(query)
        employees = session.execute_read(get_departments(query))
        # print(employees)

    # response = {"employees": employees}
    return jsonify({})


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
