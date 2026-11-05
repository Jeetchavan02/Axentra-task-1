export default function ErrorBox({ error }) {
  if (!error) return null;
  return (
    <div className="error" role="alert">
      {error.message}
      {error.fields?.length > 0 && (
        <ul>
          {error.fields.map((field) => (
            <li key={`${field.field}-${field.message}`}>
              {field.field.split(".").pop()}: {field.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
