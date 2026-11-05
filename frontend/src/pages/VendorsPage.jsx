import ResourcePage from "../components/ResourcePage";

export default function VendorsPage() {
  return (
    <ResourcePage
      title="Vendors"
      path="/vendors"
      fields={[
        { name: "name", label: "Name", required: true },
        { name: "website", label: "Website (https://...)", type: "url" },
      ]}
      columns={[
        { label: "Name", key: "name" },
        { label: "Website", render: (row) => row.website ?? "-" },
      ]}
      toBody={({ name, website }) => ({ name, website: website || null })}
    />
  );
}
