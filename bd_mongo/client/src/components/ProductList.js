import React, { useState, useEffect, useRef } from "react";

import SortButton from "./SortButton";

import "./ProductList.css";

function ProductList() {
  const firstRefresh = useRef(true);
  const [productData, setProductData] = useState([]);

  const [sortFields, setSortFields] = useState({});
  const [sortFieldShow, setSortFieldShow] = useState({});

  const refreshProducts = () => {
    const linkPrefix = "http://localhost:5000/products";
    const queryObj = {};
    Object.entries(sortFields).forEach(([field, dir]) => {
      if (dir == 1) queryObj[field] = "asc";
      if (dir == -1) queryObj[field] = "desc";
    });
    Object.entries(sortFieldShow).forEach(([field, show]) => {
      if (show) queryObj[field] ||= "show";
    });

    const query = Object.entries(queryObj).map((e) => e.join("="));

    const link = linkPrefix + (query.length ? "?" + query.join("&") : "");
    console.log(link);
    fetch(link)
      .then((response) => response.json())
      .then((json) => setProductData(json));
  };

  useEffect(() => {
    if (firstRefresh.current) {
      refreshProducts();

      firstRefresh.current = false;
    }
  }, []);

  useEffect(refreshProducts, [sortFields, sortFieldShow]);

  const sortButtonClick = (fieldName) => {
    const dir = sortFields[fieldName] || 0;
    setSortFields({ ...sortFields, [fieldName]: ((dir + 2) % 3) - 1 });
  };

  const sortShowButtonClick = (fieldName, state) => {
    setSortFieldShow({ ...sortFieldShow, [fieldName]: state });
  };

  return (
    <div>
      <div className="formFieldContainer">
        {["name", "price", "description", "amount", "unit"].map((field, i) => (
          <div key={i} className="formField">
            <SortButton
              name={field}
              fieldName={field}
              sortDir={sortFields[field] || 0}
              sortButtonClick={sortButtonClick}
            />
            <div>
              <input
                type="checkbox"
                onClick={(e) =>
                  setSortFieldShow({
                    ...sortFieldShow,
                    [field]: e.target.checked,
                  })
                }
              />
              show
            </div>
          </div>
        ))}
      </div>
      <pre>{JSON.stringify(productData, null, 2)}</pre>;
    </div>
  );
}

export default ProductList;
