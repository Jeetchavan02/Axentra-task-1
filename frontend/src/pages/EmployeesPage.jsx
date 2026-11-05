import ResourcePage from "../components/ResourcePage";

export default function EmployeesPage() {
  return (
    <ResourcePage
      title="Employees"
      path="/employees"
      fields={[
        { name: "full_name", label: "Full name", required: true },
        { name: "email", label: "Email", type: "email", required: true },
      ]}
      columns={[
        { label: "Name", key: "full_name" },
        { label: "Email", key: "email" },
      ]}
      toBody={({ full_name, email }) => ({ full_name, email })}
    />
  );
}
