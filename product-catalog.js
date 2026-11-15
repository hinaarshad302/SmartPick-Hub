/* Shared SmartPick Hub product catalogue for Home and category pages.
   Add each product once in products.json and set its department.
*/
document.addEventListener("DOMContentLoaded", () => {
  const catalogSections = [...document.querySelectorAll("[data-product-catalog]")];
  if (!catalogSections.length) return;

  fetch("products.json")
    .then(response => {
      if (!response.ok) throw new Error("Could not load product catalogue");
      return response.json();
    })
    .then(products => {
      const published = products.filter(product =>
        product.status === "published" &&
        product.name &&
        (product.affiliateUrl || product.productUrl)
      );

      catalogSections.forEach(section => {
        const grid = section.querySelector("[data-product-grid]");
        if (!grid) return;
        const department = section.dataset.productCatalog;
        const matching = department === "all"
          ? published
          : published.filter(product =>
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
          meta.textContent = [product.price, product.merchant, (product.markets || []).join(", ")].filter(Boolean).join(" · ");
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
    })
    .catch(() => {
      catalogSections.forEach(section => {
        const grid = section.querySelector("[data-product-grid]");
        if (grid) grid.innerHTML = '<p class="catalog-empty">Products are temporarily unavailable. Please try again later.</p>';
      });
    });
});
