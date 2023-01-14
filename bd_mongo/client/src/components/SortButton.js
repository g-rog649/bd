import React, { useContext } from "react";

import "./ProductList.css";

export default function SortButton({
  name,
  fieldName,
  sortDir,
  sortButtonClick,
}) {
  const sortByIcon = (
    <i className={sortDir > 0 ? "bi-sort-alpha-down" : "bi-sort-alpha-up"} />
  );

  return (
    <button
      className="sortButton"
      onClick={() => (fieldName ? sortButtonClick(fieldName) : {})}
    >
      <div>{name}</div>
      <div>{sortDir ? sortByIcon : null}</div>
    </button>
  );
}
