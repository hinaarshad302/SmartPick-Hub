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
    const databaseRecords = (data || []).map(p => ({
      ...p, affiliateUrl: p.affiliate_url || p.affiliateUrl || "",
      productUrl: p.product_url || p.productUrl || ""
    }));
    let records = databaseRecords;
    try {
      const fallback = await fetch("products.json", { cache: "no-store" });
      if (!fallback.ok) throw new Error("Could not load the JSON catalogue.");
      const jsonRecords = await fallback.json();
      const byId = new Map(jsonRecords.map(product => [product.id, product]));
      databaseRecords.forEach(product => {
        const curated = byId.get(product.id) || {};
        byId.set(product.id, {
          ...curated,
          ...product,
          image: curated.image || product.image || ""
        });
      });
      records = [...byId.values()];
    } catch (fallbackError) {
      if (!databaseRecords.length) throw error || fallbackError;
      console.warn("Using the available database products; JSON catalogue could not be loaded.", fallbackError);
    }
    if (error) console.warn("Supabase catalogue unavailable; using JSON products where available.", error);
    const liveProducts = records.filter(p =>
      p.status === "published" && p.name && (p.affiliateUrl || p.productUrl)
    );
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
    const imageFrame = document.createElement("div");
    imageFrame.className = "shop-image-frame";
    const showImageFallback = () => {
      imageFrame.replaceChildren();
      imageFrame.classList.add("is-fallback");
      imageFrame.textContent = "Product image unavailable";
    };
    if (product.image) {
      const image = document.createElement("img");
      image.alt = product.name;
      image.loading = "lazy";
      image.src = product.image;
      image.onerror = showImageFallback;
      imageFrame.appendChild(image);
    } else {
      showImageFallback();
    }
    card.appendChild(imageFrame);
    const categoryLabel = document.createElement("span");
    categoryLabel.className = "shop-category";
    categoryLabel.textContent = product.category || "Product";
    const title = document.createElement("h2");
    title.textContent = product.name;
    const description = document.createElement("p");
    description.textContent = product.description || "";
    const meta = document.createElement("div");
    meta.className = "shop-meta";
    meta.textContent = [product.price, product.merchant, (product.markets || []).join(", "), product.affiliateUrl ? "Affiliate link" : "Direct retailer link"].filter(Boolean).join(" · ");
    const link = document.createElement("a");
    const isAffiliate = Boolean(product.affiliateUrl);
    link.className = "shop-buy";
    link.href = window.smartPickOutboundUrl
      ? window.smartPickOutboundUrl(product.id, product.affiliateUrl || product.productUrl)
      : (product.affiliateUrl || product.productUrl);
    link.target = "_blank";
    link.rel = isAffiliate ? "sponsored nofollow noopener" : "noopener";
    link.textContent = isAffiliate ? "View Product" : "View on Manufacturer Site";
    // Apply the hover effect directly to every dynamically created product link.
    // Inline important styles ensure the shared page-wide link rules cannot override it.
    const applyProductLinkHover = () => {
      link.style.setProperty("background-color", "#244638", "important");
      link.style.setProperty("color", "#ffffff", "important");
      link.style.setProperty("-webkit-text-fill-color", "#ffffff", "important");
      link.style.setProperty("transform", "translateY(-3px)", "important");
      link.style.setProperty("box-shadow", "0 8px 18px rgba(36,70,56,.24)", "important");
      link.style.setProperty("outline", "2px solid #bd974d", "important");
      link.style.setProperty("outline-offset", "3px", "important");
    };
    const resetProductLinkHover = () => {
      ["background-color", "color", "-webkit-text-fill-color", "transform",
       "box-shadow", "outline", "outline-offset"].forEach(property => link.style.removeProperty(property));
    };
    link.addEventListener("pointerenter", applyProductLinkHover);
    link.addEventListener("pointerleave", resetProductLinkHover);
    link.addEventListener("focus", applyProductLinkHover);
    link.addEventListener("blur", resetProductLinkHover);
    body.append(categoryLabel, title, description, meta, link);
    card.appendChild(body);
    grid.appendChild(card);
  });
}
loadProducts();
