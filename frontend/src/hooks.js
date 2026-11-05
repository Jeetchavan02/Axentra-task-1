import { useEffect, useState } from "react";

import { api } from "./api";

/** Items for a dropdown. Limited to the API's page maximum of 100. */
export function useOptions(path, reloadKey) {
  const [items, setItems] = useState([]);
  useEffect(() => {
    api(path, { params: { limit: 100 } })
      .then((page) => setItems(page.items))
      .catch(() => setItems([]));
  }, [path, reloadKey]);
  return items;
}
