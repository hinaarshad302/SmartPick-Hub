const grid = document.getElementById("product-grid");
const searchInput = document.getElementById("product-search");
const categoryFilter = document.getElementById("category-filter");
const marketFilter = document.getElementById("market-filter");
document.getElementById("year").textContent = new Date().getFullYear();

async function loadProducts() {
  try {
    const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
    const { data, error } = await client.from("products")
      .select("id,name,category,department,markets,description,image,price,merchant,affiliate_url,product_url,status")
      .eq("status", "published")
      .order("name");
    if (error) throw error;
    const liveProducts = (data || []).map(p => ({
      ...p, affiliateUrl: p.affiliate_url || "", productUrl: p.product_url || ""
    })).filter(p => p.name && (p.affiliateUrl || p.productUrl));
    [...new Set(liveProducts.map(p => p.category).filter(Boolean))].sort().forEach(category => {
      categoryFilter.appendChild(new Option(category, category));
    });
    renderProducts(liveProducts);
    [searchInput, categoryFilter, marketFilter].forEach(control =>
      control.addEventListener("input", () => renderProducts(liveProducts))
    );
  } catch (error) {
    console.error("Shop Products load failed:", error);
    grid.innerHTML = '<div class="shop-empty">The product catalogue is not available yet. The administrator may need to complete the database setup.</div>';
  }
}

function renderProducts(products) {
  const term = searchInput.value.trim().toLowerCase();
  const category = categoryFilter.value;
  const market = marketFilter.value;
  const filtered = products.filter(product => {
    const searchable = [product.name, product.description, product.category, product.merchant].join(" ").toLowerCase();
    return searchable.includes(term) &&
      (!category || product.category === category) &&
      (!market || (product.markets || []).includes(market));
  });
  grid.replaceChildren();
  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "shop-empty";
    empty.textContent = products.length ? "No matching products found." : "Our product collection is being prepared. Please check back soon.";
    grid.appendChild(empty);
    return;
  }
  filtered.forEach(product => {
    const card = document.createElement("article");
    card.className = "shop-card";
    const body = document.createElement("div");
    body.className = "shop-card-body";
    if (product.image) {
      const image = document.createElement("img");
      image.alt = product.name;
      image.loading = "lazy";
      image.src = product.image;
      image.onerror = () => image.remove();
      card.appendChild(image);
    }
    const categoryLabel = document.createElement("span");
    categoryLabel.className = "shop-category";
    categoryLabel.textContent = product.category || "Product";
    const title = document.createElement("h2");
    title.textContent = product.name;
    const description = document.createElement("p");
    description.textContent = product.description || "";
    const meta = document.createElement("div");
    meta.className = "shop-meta";
    meta.textContent = [product.price, product.merchant, (product.markets || []).join(", ")].filter(Boolean).join(" · ");
    const link = document.createElement("a");
    const isAffiliate = Boolean(product.affiliateUrl);
    link.className = "shop-buy";
    link.href = product.affiliateUrl || product.productUrl;
    link.target = "_blank";
    link.rel = isAffiliate ? "sponsored nofollow noopener" : "noopener";
    link.textContent = isAffiliate ? "View Product" : "View on Manufacturer Site";
    body.append(categoryLabel, title, description, meta, link);
    card.appendChild(body);
    grid.appendChild(card);
  });
}
loadProducts();
