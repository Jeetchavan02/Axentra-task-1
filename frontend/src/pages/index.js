import EmployeesPage from "./EmployeesPage";
import SubscriptionsPage from "./SubscriptionsPage";
import VendorsPage from "./VendorsPage";

// Screens shown in the sidebar, in order.
export const PAGES = [
  { label: "Subscriptions", component: SubscriptionsPage },
  { label: "Vendors", component: VendorsPage },
  { label: "Employees", component: EmployeesPage },
];
