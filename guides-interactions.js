document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.getElementById("guide-dialog");
  if (!dialog) return;
  const title = document.getElementById("guide-dialog-title");
  const label = document.getElementById("guide-dialog-label");
  const description = document.getElementById("guide-dialog-description");
  const closeButton = dialog.querySelector(".guide-dialog-close");
  let lastTrigger = null;

  const topicContent = {
    "01": {
      label: "AI WRITING TOOLS",
      title: "How to Choose AI Writing Tools",
      intro: "Choose a writing assistant based on the work you actually need to do—not just its popularity.",
      points: [
        ["Writing quality", "Test the tool with your own prompts. Check clarity, accuracy, tone, editing quality and whether it repeats or invents information."],
        ["Language support", "Check the languages and scripts you use, including Urdu or other regional languages. Test spelling, grammar and natural phrasing."],
        ["Features and workflow", "Compare drafting, rewriting, summarising, research assistance, document export and integrations. Make sure the features fit your routine."],
        ["Ease of use", "Look for a clear interface, useful controls and a workflow that is comfortable for beginners."],
        ["Pricing and limits", "Compare free usage limits, paid plan limits, renewal costs and cancellation terms. Do not upgrade until you have tested the free option."],
        ["Privacy", "Avoid entering confidential personal, customer or business information unless the provider's data policy and settings are suitable."]
      ],
      takeaway: "Smart tip: test two or three tools using the same real writing task, then compare the results side by side."
    },
    "02": {
      label: "AI DESIGN TOOLS",
      title: "Choosing AI Design Tools",
      intro: "The right design tool should help you create the type of visual content you need and give you enough control to refine it.",
      points: [
        ["Templates and output types", "Check whether the tool supports your needs, such as social posts, presentations, banners, logos or product graphics."],
        ["Editing flexibility", "Find out whether you can change text, colours, fonts, layout, layers and individual design elements after generation."],
        ["Export options", "Check available formats, image dimensions, resolution, transparency and whether downloads add watermarks."],
        ["Ease of use", "Try the editor yourself. Clear controls and beginner-friendly templates can save time."],
        ["Usage and licensing", "Review free and paid limits, commercial-use terms, asset licensing and any restrictions on generated content."],
        ["Privacy", "Understand how uploaded photos, brand assets and prompts are stored and used."]
      ],
      takeaway: "Smart tip: create one sample design and test editing and downloading before paying for a subscription."
    },
    "03": {
      label: "PRODUCTIVITY SOFTWARE",
      title: "Compare Productivity Software",
      intro: "Productivity software should make your work easier, not add unnecessary complexity.",
      points: [
        ["Task management", "Compare task lists, projects, priorities, due dates, reminders and progress tracking."],
        ["Team collaboration", "Check comments, file sharing, assignments, permissions and real-time collaboration."],
        ["Integrations", "Make sure the software connects with the email, calendar, storage and communication tools you already use."],
        ["Ease of use", "Consider setup time, learning curve, mobile access and whether the interface stays manageable as work grows."],
        ["Privacy and security", "Review access controls, authentication, data export, backups and the provider's privacy policy."],
        ["Total cost", "Compare per-user pricing, storage or usage limits, billing periods and the cost of adding team members."]
      ],
      takeaway: "Smart tip: shortlist tools against your team's must-have requirements and test them with a small real project."
    },
    "04": {
      label: "PRICING GUIDE",
      title: "Free vs Paid Tools",
      intro: "A paid plan is worthwhile only when its additional value solves a real problem for you.",
      points: [
        ["Free plan limits", "Check monthly usage, project limits, storage, exports, advertisements and access to core features."],
        ["Paid features", "Identify exactly which features become available after upgrading and whether you will use them regularly."],
        ["Recurring costs", "Compare monthly and annual billing, taxes, renewal dates, cancellation rules and price changes."],
        ["Trial conditions", "Check whether a trial requires a payment method and when billing starts. Set a reminder before the trial ends."],
        ["Alternatives", "Compare other tools and consider whether a free or lower-cost option already meets your needs."],
        ["Upgrade decision", "Estimate the time saved or work improved, then compare that benefit with the full subscription cost."]
      ],
      takeaway: "Smart tip: start with the free plan, track what is missing, and upgrade only when a specific limitation affects your work."
    }
  };
  const checklistContent = {
    "01": {
      label: "BEFORE YOU BUY",
      title: "Your Actual Needs",
      intro: "Start by defining the problem. A product with many features is not automatically the right choice.",
      points: [
        ["Define the task", "Write down what you want the product or tool to help you accomplish."],
        ["Identify must-haves", "Separate essential features from optional extras."],
        ["Consider who will use it", "Think about skill level, accessibility, language, device compatibility and number of users."],
        ["Set a realistic budget", "Decide what you can spend, including subscriptions, accessories or maintenance."]
      ],
      takeaway: "Ask yourself: what exact problem will this purchase solve?"
    },
    "02": {
      label: "BEFORE YOU BUY",
      title: "Features and Limitations",
      intro: "Check the full feature set and understand what the product cannot do.",
      points: [
        ["Verify specifications", "Use the manufacturer's or provider's official information to confirm important details."],
        ["Check compatibility", "Confirm operating system, device, size, connectivity, region and other requirements."],
        ["Understand limitations", "Look for usage caps, missing features, required accessories and restrictions."],
        ["Read independent feedback", "Compare recent user reviews and look for recurring strengths or problems."]
      ],
      takeaway: "Do not rely on a headline feature alone—check the details that affect your use."
    },
    "03": {
      label: "BEFORE YOU BUY",
      title: "Pricing and Value",
      intro: "Compare the complete cost rather than focusing only on the displayed starting price.",
      points: [
        ["Compare total cost", "Include taxes, shipping, accessories, installation and recurring subscriptions where applicable."],
        ["Check the billing period", "Understand monthly versus annual billing, automatic renewal and cancellation terms."],
        ["Compare alternatives", "Check products with similar features and consider whether a less expensive option is enough."],
        ["Review warranty and returns", "Understand warranty coverage, return windows, refund rules and support availability."]
      ],
      takeaway: "The best value is the option that meets your needs at a fair total cost."
    },
    "04": {
      label: "BEFORE YOU BUY",
      title: "Privacy and Security",
      intro: "For connected products and software, understand what information is collected and how it is protected.",
      points: [
        ["Review the privacy policy", "Check what data is collected, why it is collected and how long it is retained."],
        ["Check permissions", "Question access to contacts, camera, microphone, location or files when it is not needed."],
        ["Look for security controls", "Check account protection, multi-factor authentication, encryption information and update support."],
        ["Understand data control", "Find out whether you can export, correct or delete your data and close your account."]
      ],
      takeaway: "Avoid sharing sensitive information until you understand the provider's privacy and security practices."
    }
  };

  function openDialog(content, trigger, isChecklist) {
    lastTrigger = trigger;
    label.textContent = content.label;
    title.textContent = content.title;
    description.replaceChildren();
    const intro = document.createElement("p");
    intro.className = "guide-dialog-intro";
    intro.textContent = content.intro;
    description.appendChild(intro);
    const list = document.createElement("div");
    list.className = "guide-dialog-points";
    content.points.forEach(([heading, detail], index) => {
      const item = document.createElement("article");
      item.className = "guide-dialog-point";
      const number = document.createElement("span");
      number.className = "guide-dialog-point-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const copy = document.createElement("div");
      const h3 = document.createElement("h3");
      h3.textContent = heading;
      const p = document.createElement("p");
      p.textContent = detail;
      copy.append(h3, p);
      item.append(number, copy);
      list.appendChild(item);
    });
    description.appendChild(list);
    const tip = document.createElement("p");
    tip.className = "guide-dialog-tip";
    tip.textContent = content.takeaway;
    description.appendChild(tip);
    if (content.title === "How to Choose AI Writing Tools") {
      const toolsLink = document.createElement("a");
      toolsLink.className = "guide-dialog-tools-link";
      toolsLink.href = "#ai-writing-tools";
      toolsLink.textContent = "Explore actual AI writing tools ↓";
      toolsLink.addEventListener("click", closeDialog);
      description.appendChild(toolsLink);
    }
    dialog.hidden = false;
    document.body.classList.add("guide-dialog-open");
    closeButton.focus();
  }
  function closeDialog() {
    if (dialog.hidden) return;
    dialog.hidden = true;
    document.body.classList.remove("guide-dialog-open");
    if (lastTrigger) lastTrigger.focus();
  }
  document.querySelectorAll("[data-guide-topic]").forEach(button => {
    button.addEventListener("click", () => {
      const content = topicContent[button.dataset.guideTopic];
      if (content) openDialog(content, button, false);
    });
  });
  document.querySelectorAll("[data-checklist-topic]").forEach(button => {
    button.addEventListener("click", () => {
      const content = checklistContent[button.dataset.checklistTopic];
      if (content) openDialog(content, button, true);
    });
  });
  closeButton.addEventListener("click", closeDialog);
  dialog.addEventListener("click", event => {
    if (event.target === dialog) closeDialog();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !dialog.hidden) closeDialog();
  });
});
