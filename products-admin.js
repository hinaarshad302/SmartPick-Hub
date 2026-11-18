const adminClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
const loginPanel = document.getElementById("admin-login-panel");
const editorPanel = document.getElementById("admin-editor-panel");
const message = document.getElementById("admin-message");
const picker = document.getElementById("product-picker");
const form = document.getElementById("product-form");
const deleteButton = document.getElementById("product-delete-button");
let products = [];

const fields = {
  id: "product-id", name: "product-name", department: "product-department",
  category: "product-category", merchant: "product-merchant", price: "product-price",
  description: "product-description", image: "product-image", product_url: "product-url",
  affiliate_url: "product-affiliate", markets: "product-markets", status: "product-status"
};
const value = key => document.getElementById(fields[key]).value.trim();
const setValue = (key, val = "") => { document.getElementById(fields[key]).value = val ?? ""; };

function showMessage(text, isError = false) {
  message.textContent = text;
  message.style.color = isError ? "#9b2525" : "#244638";
}
function validHttps(url) {
  if (!url) return true;
  try { return new URL(url).protocol === "https:"; } catch { return false; }
}
function clearForm() {
  form.reset();
  setValue("status", "draft");
  picker.value = "";
  deleteButton.disabled = true;
}
function fillForm(product) {
  Object.keys(fields).forEach(key => {
    const val = key === "markets" ? (product.markets || []).join(", ") : product[key];
    setValue(key, val);
  });
  deleteButton.disabled = false;
}
async function loadCatalogue() {
  const { data, error } = await adminClient.from("products").select("*").order("name");
  if (error) throw error;
  products = data || [];
  picker.replaceChildren(new Option("＋ Add a new product", ""));
  products.forEach(product => picker.add(new Option(product.name + " · " + product.status, product.id)));
}
async function checkAdmin() {
  const { data: { session }, error } = await adminClient.auth.getSession();
  if (error) throw error;
  if (!session) {
    loginPanel.hidden = false;
    editorPanel.hidden = true;
    return;
  }
  const { data, error: adminError } = await adminClient
    .from("smartpick_admins").select("user_id").eq("user_id", session.user.id).maybeSingle();
  if (adminError) throw adminError;
  if (!data) {
    await adminClient.auth.signOut();
    throw new Error("This account is not authorised as an administrator. Ask the project owner to grant admin access in Supabase.");
  }
  loginPanel.hidden = true;
  editorPanel.hidden = false;
  await loadCatalogue();
  showMessage("Admin access confirmed. Catalogue loaded.");
}
document.getElementById("admin-login-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = document.getElementById("admin-login-button");
  button.disabled = true;
  showMessage("Signing in...");
  try {
    const { error } = await adminClient.auth.signInWithPassword({
      email: document.getElementById("admin-email").value.trim(),
      password: document.getElementById("admin-password").value
    });
    if (error) throw error;
    await checkAdmin();
  } catch (error) { showMessage(error.message || "Sign in failed.", true); }
  finally { button.disabled = false; }
});
picker.addEventListener("change", () => {
  const product = products.find(item => item.id === picker.value);
  if (product) fillForm(product); else clearForm();
});
document.getElementById("product-new-button").addEventListener("click", clearForm);
document.getElementById("admin-logout-button").addEventListener("click", async () => {
  await adminClient.auth.signOut();
  products = [];
  editorPanel.hidden = true;
  loginPanel.hidden = false;
  showMessage("Signed out.");
});
form.addEventListener("submit", async event => {
  event.preventDefault();
  const record = {};
  Object.keys(fields).forEach(key => { record[key] = value(key); });
  record.markets = record.markets.split(",").map(item => item.trim()).filter(Boolean);
  if (!record.affiliate_url && !record.product_url) {
    showMessage("Add a manufacturer/retailer URL or an approved affiliate URL.", true); return;
  }
  if (record.status === "published" && !record.image) {
    showMessage("Add the exact product photo before publishing this product.", true); return;
  }
  if (![record.image, record.product_url, record.affiliate_url].every(validHttps)) {
    showMessage("Image and product links must use HTTPS URLs.", true); return;
  }
  const button = document.getElementById("product-save-button");
  button.disabled = true;
  showMessage("Saving product...");
  try {
    const { error } = await adminClient.from("products").upsert(record, { onConflict: "id" });
    if (error) throw error;
    await loadCatalogue();
    picker.value = record.id;
    const saved = products.find(item => item.id === record.id);
    if (saved) fillForm(saved);
    showMessage("Product saved successfully.");
  } catch (error) { showMessage(error.message || "Could not save product.", true); }
  finally { button.disabled = false; }
});
deleteButton.addEventListener("click", async () => {
  const id = picker.value;
  if (!id || !window.confirm("Permanently delete this product?")) return;
  deleteButton.disabled = true;
  try {
    const { error } = await adminClient.from("products").delete().eq("id", id);
    if (error) throw error;
    await loadCatalogue();
    clearForm();
    showMessage("Product deleted.");
  } catch (error) { showMessage(error.message || "Could not delete product.", true); }
  finally { deleteButton.disabled = !picker.value; }
});
checkAdmin().catch(error => {
  showMessage(error.message || "Admin page could not initialise. Apply the product catalogue migration first.", true);
});
