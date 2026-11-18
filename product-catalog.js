/* Shared SmartPick Hub catalogue: every published product is shown on Home,
   and only its assigned department is shown on the matching category page. */
document.addEventListener("DOMContentLoaded", async () => {
  const sections = [...document.querySelectorAll("[data-product-catalog]")];
  if (!sections.length) return;

  const normalize = value => String(value || "").trim().toLowerCase().replace(/\\s+/g, " ");

  async function loadProducts() {
    // Start both sources together, but return the local JSON catalogue first.
    const localPromise = fetch("products.json")
      .then(response => {
        if (!response.ok) throw new Error("Could not load the product catalogue.");
        return response.json();
      });
    const databasePromise = (async () => {
      try {
        if (!window.supabase || typeof window.supabase.createClient !== "function") return [];
        const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
        const { data, error } = await client.from("products")
          .select("id,name,category,department,markets,description,image,price,merchant,affiliate_url,product_url,status")
          .eq("status", "published")
          .order("name");
        if (error) throw error;
        return (data || []).map(product => ({
          ...product,
          affiliateUrl: product.affiliate_url || product.affiliateUrl || "",
          productUrl: product.product_url || product.productUrl || ""
        }));
      } catch (error) {
        console.warn("Using local products; database refresh unavailable.", error);
        return [];
      }
    })();

    try {
      const localRecords = await localPromise;
      return { records: localRecords, databasePromise };
    } catch (localError) {
      const databaseRecords = await databasePromise;
      if (databaseRecords.length) {
        return { records: databaseRecords, databasePromise: Promise.resolve([]) };
      }
      throw localError;
    }
  }

  try {
    const { records, databasePromise } = await loadProducts();
    const renderCatalog = sourceRecords => {
    const published = sourceRecords.filter(product =>
      product.status === "published" &&
      product.name &&
      (product.affiliateUrl || product.productUrl || product.affiliate_url || product.product_url)
    );

    sections.forEach(section => {
      const grid = section.querySelector("[data-product-grid]");
      if (!grid) return;

      const department = normalize(section.dataset.productCatalog);
      const matching = department === "all"
        ? published
        : published.filter(product => normalize(product.department) === department);

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

        const imageFrame = document.createElement("div");
        imageFrame.className = "catalog-image-frame";
        const showImageFallback = () => {
          imageFrame.replaceChildren();
          imageFrame.classList.add("is-fallback");
          imageFrame.textContent = "Product image unavailable";
        };
        if (product.image) {
          const image = document.createElement("img");
          image.src = product.image;
          image.alt = product.name;
          image.loading = "lazy";
          image.decoding = "async";
          image.width = 320;
          image.height = 180;
          image.onerror = showImageFallback;
          imageFrame.appendChild(image);
        } else {
          showImageFallback();
        }
        card.appendChild(imageFrame);

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
        const affiliateUrl = product.affiliateUrl || product.affiliate_url || "";
        const productUrl = product.productUrl || product.product_url || "";
        meta.textContent = [
          product.price,
          product.merchant,
          (product.markets || []).join(", "),
          affiliateUrl ? "Affiliate link" : "Direct retailer link"
        ].filter(Boolean).join(" · ");

        const link = document.createElement("a");
        link.className = "catalog-buy";
        link.href = window.smartPickOutboundUrl
          ? window.smartPickOutboundUrl(product.id, affiliateUrl || productUrl)
          : (affiliateUrl || productUrl);
        link.target = "_blank";
        link.rel = affiliateUrl ? "sponsored nofollow noopener" : "noopener";
        link.textContent = affiliateUrl ? "View Product" : "View on Manufacturer Site";

        body.append(category, title, description, meta, link);
        card.appendChild(body);
        grid.appendChild(card);
      });
    });
    };
    renderCatalog(records);
    databasePromise.then(databaseRecords => {
      if (!databaseRecords.length) return;
      const byId = new Map(records.map(product => [product.id, product]));
      databaseRecords.forEach(product => {
        const local = byId.get(product.id) || {};
        byId.set(product.id, { ...local, ...product, image: local.image || product.image || "" });
      });
      renderCatalog([...byId.values()]);
    });
  } catch (error) {
    console.error("SmartPick catalogue load failed:", error);
    sections.forEach(section => {
      const grid = section.querySelector("[data-product-grid]");
      if (grid) {
        const message = document.createElement("p");
        message.className = "catalog-empty";
        message.textContent = "The product catalogue is temporarily unavailable. Please try again shortly.";
        grid.replaceChildren(message);
      }
    });
  }
});
