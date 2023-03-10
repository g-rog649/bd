const { ObjectID } = require("bson");
const express = require("express");
const productRoutes = express.Router();
const dbo = require("../db/conn");
const ObjectId = require("mongodb").ObjectId;

const productFields = {
  name: "string",
  price: "number",
  description: "string",
  amount: "number",
  unit: "string",
};

// Get all the products from the database
productRoutes.route("/products").get((req, res) => {
  const dbConnect = dbo.getDb("shop");
  const routeOptions = Object.keys(productFields).map((field) => [
    field,
    req.query[field],
  ]);
  const projectOptions = {};
  const sortOptions = {};
  let projectEmpty = true;
  let sortEmpty = true;

  routeOptions.forEach(([field, option]) => {
    switch (option) {
      case "hide":
        projectOptions[field] = 0;
        projectEmpty = false;
        break;

      case "show":
        projectOptions[field] = 1;
        projectEmpty = false;
        break;

      case "asc":
        sortOptions[field] = 1;
        sortEmpty = false;
        break;

      case "desc":
        sortOptions[field] = -1;
        sortEmpty = false;
        break;
    }
  });

  const options = [];

  if (!projectEmpty && !sortEmpty) {
    for (const field in sortOptions) {
      projectOptions[field] = 1;
    }
  }
  if (!projectEmpty) options.push({ $project: projectOptions });
  if (!sortEmpty) options.push({ $sort: sortOptions });

  dbConnect
    .collection("products")
    .aggregate(options)
    .toArray()
    .then(
      (result) => res.json(result),
      (err) => {
        throw err;
      }
    );
});

// Add a product to the database
productRoutes.route("/product/add").post((req, res) => {
  const dbConnect = dbo.getDb("shop");

  // Try to add the product
  dbConnect
    .collection("products")
    .findOne({ name: req.body.name })
    .then(
      (res) =>
        // Check if name unique
        new Promise((resolve, reject) => (res === null ? resolve() : reject())),
      (err) => {
        throw err;
      }
    )
    .then(
      // Insert the product
      () => {
        const addedProduct = Object.fromEntries(
          Object.keys(productFields).map((field) => [field, req.body[field]])
        );

        dbConnect
          .collection("products")
          .insertOne(addedProduct, (err, response) => {
            if (err) throw err;
            res.json(response);
          });
      },
      // Name not unique
      () => res.json({ error: "Product already exists!" })
    );
});

// Edit a product from the database
productRoutes.route("/products/:id").put((req, res) => {
  const dbConnect = dbo.getDb("shop");

  const updateFields = {};
  const errors = {};
  let noErrors = true;

  if (!ObjectID.isValid(req.params.id)) {
    errors.id = "wrong ID format";
    res.json({ errors });
    return;
  }

  Object.entries(productFields).forEach(([field, type]) => {
    const bodyValue = req.body[field];
    if (typeof bodyValue === type) {
      updateFields[field] = bodyValue;
    } else if (typeof bodyValue !== "undefined") {
      errors[field] = `not a ${type}`;
      noErrors = false;
    }
  });

  if (noErrors) {
    dbConnect
      .collection("products")
      .updateOne({ _id: new ObjectId(req.params.id) }, { $set: updateFields })
      .then(
        (result) => res.json(result),
        (err) => {
          throw err;
        }
      );
  } else {
    res.json({ errors });
  }
});

// Remove a product from the database
productRoutes.route("/products/:id").delete((req, res) => {
  const dbConnect = dbo.getDb("shop");

  if (!ObjectID.isValid(req.params.id)) {
    res.json({ error: "wrong ID format" });
    return;
  }

  dbConnect
    .collection("products")
    .deleteOne({ _id: new ObjectId(req.params.id) })
    .then(
      (result) => {
        console.log(`Deleted product with ID ${req.params.id}`);
        res.json(result);
      },
      (err) => {
        throw err;
      }
    );
});

// Remove all products from the database
productRoutes.route("/products").delete((req, res) => {
  const dbConnect = dbo.getDb("shop");

  dbConnect
    .collection("products")
    .deleteMany({})
    .then(
      (result) => {
        console.log(`Deleted all products`);
        res.json(result);
      },
      (err) => {
        throw err;
      }
    );
});

// Generate a product report
productRoutes.route("/products/report").get((req, res) => {
  const dbConnect = dbo.getDb("shop");

  const result = dbConnect
    .collection("products")
    .aggregate([
      {
        $unset: "description",
      },
      {
        $addFields: {
          allPrice: {
            $trunc: [{ $sum: { $multiply: ["$price", "$amount"] } }, 2],
          },
        },
      },
    ])
    .sort({ allPrice: -1 })
    .toArray()
    .then(
      (result) => res.json(result),
      (err) => {
        throw err;
      }
    );
});

module.exports = productRoutes;
