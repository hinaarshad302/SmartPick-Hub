/* Shared SmartPick Hub catalogue powered by Supabase.
   Product records are managed through products-admin.html.
*/
document.addEventListener("DOMContentLoaded", async () => {
  const sections = [...document.querySelectorAll("[data-product-catalog]")];
  if (!sections.length) return;
  try {
    const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
    const { data, error } = await client.from("products")
      .select("id,name,category,department,markets,description,image,price,merchant,affiliate_url,product_url,status")
      .eq("status", "published")
      .order("name");
    let records;
    if (error) {
      console.warn("Supabase catalogue is not ready; using the temporary JSON catalogue.", error);
      const fallback = await fetch("products.json");
      if (!fallback.ok) throw error;
      records = await fallback.json();
    } else {
      records = (data || []).map(product => ({
        ...product,
        affiliateUrl: product.affiliate_url || "",
        productUrl: product.product_url || ""
      }));
    }
    const published = records.filter(product =>
      product.status === "published" && product.name && (product.affiliateUrl || product.productUrl)
    );

    sections.forEach(section => {
      const grid = section.querySelector("[data-product-grid]");
      if (!grid) return;
      const department = section.dataset.productCatalog;
      const matching = department === "all" ? published : published.filter(product =>
        String(product.department || "").toLowerCase() === department.toLowerCase()
      );
      grid.replaceChildren();
      if (!matching.length) {
        const empty = document.createElement("p");
        empty.className = "catalog-empty";
        empty.textContent = "We're preparing product picks for this category. Please check back soon.";
        grid.appendChild(empty);
        return;
      }
      matching.forEach(product => {
        const card = document.createElement("article");
        card.className = "catalog-product-card";
        if (product.image) {
          const image = document.createElement("img");
          image.src = product.image;
          image.alt = product.name;
          image.loading = "lazy";
          image.onerror = () => image.remove();
          card.appendChild(image);
        }
        const body = document.createElement("div");
        body.className = "catalog-product-card-body";
        const category = document.createElement("span");
        category.className = "catalog-category";
        category.textContent = product.category || product.department || "Product";
        const title = document.createElement("h3");
        title.textContent = product.name;
        const description = document.createElement("p");
        description.textContent = product.description || "";
        const meta = document.createElement("p");
        meta.className = "catalog-meta";
        meta.textContent = [product.price, product.merchant, (product.markets || []).join(", "), product.affiliateUrl ? "Affiliate link" : "Direct retailer link"].filter(Boolean).join(" · ");
        const link = document.createElement("a");
        const isAffiliate = Boolean(product.affiliateUrl);
        link.className = "catalog-buy";
        link.href = product.affiliateUrl || product.productUrl;
        link.target = "_blank";
        link.rel = isAffiliate ? "sponsored nofollow noopener" : "noopener";
        link.textContent = isAffiliate ? "View Product" : "View on Manufacturer Site";
        body.append(category, title, description, meta, link);
        card.appendChild(body);
        grid.appendChild(card);
      });
    });
  } catch (error) {
    console.error("SmartPick catalogue load failed:", error);
    sections.forEach(section => {
      const grid = section.querySelector("[data-product-grid]");
      if (grid) grid.innerHTML = '<p class="catalog-empty">The product catalogue is not available yet. The administrator may need to complete the database setup.</p>';
    });
  }
});
