const grid = document.getElementById("product-grid");
const searchInput = document.getElementById("product-search");
const categoryFilter = document.getElementById("category-filter");
const marketFilter = document.getElementById("market-filter");
document.getElementById("year").textContent = new Date().getFullYear();

async function fetchDatabaseProducts() {
  if (!window.supabase || typeof window.supabase.createClient !== "function") return [];
  try {
    const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
    const { data, error } = await client.from("products")
      .select("id,name,category,department,markets,description,image,price,merchant,affiliate_url,product_url,status")
      .eq("status", "published")
      .order("name");
    if (error) throw error;
    return (data || []).map(p => ({
      ...p,
      affiliateUrl: p.affiliate_url || p.affiliateUrl || "",
      productUrl: p.product_url || p.productUrl || ""
    }));
  } catch (error) {
    console.warn("Using the fast local product catalogue; database refresh unavailable.", error);
    return [];
  }
}

function mergeProductSources(localProducts, databaseProducts) {
  const byId = new Map(localProducts.map(product => [product.id, product]));
  databaseProducts.forEach(product => {
    const local = byId.get(product.id) || {};
    byId.set(product.id, {
      ...local,
      ...product,
      image: local.image || product.image || ""
    });
  });
  return [...byId.values()];
}

async function loadProducts() {
  try {
    // Show the bundled catalogue first instead of making visitors wait for Supabase.
    const localPromise = fetch("products.json")
      .then(response => {
        if (!response.ok) throw new Error("Could not load the local product catalogue.");
        return response.json();
      });
    const databasePromise = fetchDatabaseProducts();

    let localProducts = [];
    try {
      localProducts = await localPromise;
      const initialProducts = localProducts.filter(p =>
        p.status === "published" && p.name && (p.affiliateUrl || p.productUrl)
      );
      renderProducts(initialProducts);
    } catch (localError) {
      const databaseProducts = await databasePromise;
      if (!databaseProducts.length) throw localError;
      localProducts = databaseProducts;
      renderProducts(localProducts.filter(p =>
        p.status === "published" && p.name && (p.affiliateUrl || p.productUrl)
      ));
      return;
    }

    // Refresh from the database in the background; never block the first render.
    databasePromise.then(databaseProducts => {
      if (!databaseProducts.length) return;
      const updated = mergeProductSources(localProducts, databaseProducts).filter(p =>
        p.status === "published" && p.name && (p.affiliateUrl || p.productUrl)
      );
      renderProducts(updated);
    });
  } catch (error) {
    console.error("Shop Products load failed:", error);
    grid.innerHTML = '<div class="shop-empty">The product catalogue is temporarily unavailable. Please refresh the page shortly.</div>';
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
  filtered.forEach((product, index) => {
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
      image.loading = index === 0 ? "eager" : "lazy";
      if (index === 0) image.fetchPriority = "high";
      image.decoding = "async";
      image.width = 320;
      image.height = 180;
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
// Reliable delegated hover handling for every product link, including dynamically filtered cards.
const productGrid = document.getElementById("product-grid");
if (productGrid) {
  const setProductHover = (link) => {
    if (!link || !link.matches("a.shop-buy")) return;
    link.style.setProperty("background-color", "#244638", "important");
    link.style.setProperty("color", "#ffffff", "important");
    link.style.setProperty("-webkit-text-fill-color", "#ffffff", "important");
    link.style.setProperty("transform", "translateY(-3px)", "important");
    link.style.setProperty("box-shadow", "0 8px 18px rgba(36,70,56,.24)", "important");
    link.style.setProperty("outline", "2px solid #bd974d", "important");
    link.style.setProperty("outline-offset", "3px", "important");
  };
  const clearProductHover = (link) => {
    if (!link || !link.matches("a.shop-buy")) return;
    ["background-color", "color", "-webkit-text-fill-color", "transform",
     "box-shadow", "outline", "outline-offset"].forEach(property => link.style.removeProperty(property));
  };
  productGrid.addEventListener("mouseover", event => {
    const link = event.target.closest("a.shop-buy");
    if (link && !link.contains(event.relatedTarget)) setProductHover(link);
  });
  productGrid.addEventListener("mouseout", event => {
    const link = event.target.closest("a.shop-buy");
    if (link && !link.contains(event.relatedTarget)) clearProductHover(link);
  });
  productGrid.addEventListener("focusin", event => setProductHover(event.target.closest("a.shop-buy")));
  productGrid.addEventListener("focusout", event => clearProductHover(event.target.closest("a.shop-buy")));
}

loadProducts();
