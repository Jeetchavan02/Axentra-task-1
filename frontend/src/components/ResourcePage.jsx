import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api";
import ErrorBox from "./ErrorBox";

const PAGE_SIZE = 10;

function Field({ field, value, onChange }) {
  const props = {
    name: field.name,
    value: value ?? "",
    required: field.required,
    onChange: (event) => onChange(field.name, event.target.value),
  };
  return (
    <label>
      {field.label}
      {field.options ? (
        <select {...props}>
          {field.placeholder && <option value="">{field.placeholder}</option>}
          {field.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : (
        <input {...props} type={field.type ?? "text"} min={field.min} step={field.step} />
      )}
    </label>
  );
}

/** List, search, create, edit and delete for one API resource, driven by its field config. */
export default function ResourcePage({
  title,
  path,
  fields,
  columns,
  defaults = {},
  filters = [],
  toBody = (values) => values,
  rowActions,
  onChanged,
}) {
  const [page, setPage] = useState(null);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [filterValues, setFilterValues] = useState({});
  const [editing, setEditing] = useState(null); // null, "new", or the row being edited
  const [values, setValues] = useState({});
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const latestRequest = useRef(0);

  const load = useCallback(async () => {
    // Only the newest request may update the screen, so a slow older search can't overwrite it.
    const request = ++latestRequest.current;
    try {
      const result = await api(path, {
        params: { limit: PAGE_SIZE, offset, search, ...filterValues },
      });
      if (request === latestRequest.current) setPage(result);
    } catch (err) {
      if (request === latestRequest.current) setError(err);
    }
  }, [path, offset, search, filterValues]);

  useEffect(() => {
    load();
  }, [load]);

  const openForm = (row) => {
    setError(null);
    setEditing(row ?? "new");
    setValues(row ?? { ...defaults });
  };

  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body = toBody(values);
      if (editing === "new") await api(path, { method: "POST", body });
      else await api(`${path}/${editing.id}`, { method: "PUT", body });
      setEditing(null);
      await load();
      onChanged?.();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  async function remove(row) {
    if (!window.confirm(`Delete this ${title.toLowerCase().replace(/s$/, "")}?`)) return;
    setError(null);
    try {
      await api(`${path}/${row.id}`, { method: "DELETE" });
      // Step back if that was the only row on the last page.
      if (page.items.length === 1 && offset > 0) setOffset(Math.max(0, offset - PAGE_SIZE));
      else await load();
      onChanged?.();
    } catch (err) {
      setError(err);
    }
  }

  const resetToFirstPage = () => setOffset(0);

  return (
    <>
      <div className="toolbar">
        <h1>{title}</h1>
        {filters.map((filter) => (
          <select
            key={filter.name}
            aria-label={filter.label}
            value={filterValues[filter.name] ?? ""}
            onChange={(event) => {
              setFilterValues({ ...filterValues, [filter.name]: event.target.value });
              resetToFirstPage();
            }}
          >
            <option value="">{filter.label}: all</option>
            {filter.options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ))}
        <input
          type="search"
          placeholder="Search"
          aria-label={`Search ${title.toLowerCase()}`}
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            resetToFirstPage();
          }}
        />
        <button className="primary" onClick={() => openForm()}>
          Add
        </button>
      </div>

      <ErrorBox error={error} />

      {editing && (
        <form className="card" onSubmit={save}>
          <h2>{editing === "new" ? "Add" : "Edit"}</h2>
          <div className="form-grid">
            {fields.map((field) => (
              <Field
                key={field.name}
                field={field}
                value={values[field.name]}
                onChange={(name, value) => setValues({ ...values, [name]: value })}
              />
            ))}
          </div>
          <div className="form-actions">
            <button className="primary" disabled={busy}>
              Save
            </button>
            <button type="button" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      {page && page.items.length === 0 && (
        <p className="muted">{search ? "No matches." : "Nothing here yet. Click Add to create one."}</p>
      )}

      {page && page.items.length > 0 && (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column.label} className={column.numeric ? "num" : ""}>
                      {column.label}
                    </th>
                  ))}
                  <th />
                </tr>
              </thead>
              <tbody>
                {page.items.map((row) => (
                  <tr key={row.id}>
                    {columns.map((column) => (
                      <td key={column.label} className={column.numeric ? "num" : ""}>
                        {column.render ? column.render(row) : row[column.key]}
                      </td>
                    ))}
                    <td className="actions">
                      {rowActions?.(row)}
                      <button onClick={() => openForm(row)}>Edit</button>
                      <button className="danger" onClick={() => remove(row)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pager">
            <span className="muted">
              {offset + 1}-{offset + page.items.length} of {page.total}
            </span>
            <button disabled={offset === 0} onClick={() => setOffset(offset - PAGE_SIZE)}>
              Previous
            </button>
            <button
              disabled={offset + PAGE_SIZE >= page.total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </>
  );
}
