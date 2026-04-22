/skill ui-ux-pro-max
/skill impeccable

You are tasked with a complete, $100K+ enterprise-grade frontend redesign of "DeepShield", an Explainable AI-based multimodal misinformation detection web platform. Your goal is to build a hyper-premium, performant, and beautifully animated web application.

### 1. PROJECT CONTEXT & DESIGN PHILOSOPHY
* **Brand Vibe:** Forensic, Premium, and Calm. DeepShield is a high-stakes trust instrument. It must feel like an expensive, highly capable enterprise tool (think Vercel, Stripe, or Linear) crossed with Apple's cinematic product pages.
* **Theme:** Dark Mode First. Use a graphite and deep indigo canvas with glassmorphism (translucent panels, background blurs). 
* **User Psychology (Progressive Disclosure):** Deliver a calming, simple, and definitive verdict immediately. Hide the high-density forensic evidence (Grad-CAM++ heatmaps, EXIF tables, LLM breakdowns) behind elegant expansions for researchers.
* **Anti-References:** Absolutely NO generic "AI-slop", NO standard Material/Bootstrap admin dashboards, and NO chaotic "VirusTotal" walls of data. No sensationalist red sirens.

### 2. WORKFLOW & EXECUTION PROCESS
Before writing a single line of code, execute the following workflow:
1. **Analyze Reference Website:** Fetch and extract design ideas, layout structures, and premium UI patterns from `https://specifyapp.com/?ref=landingfolio`. (If you are unable to access it via Puppeteer or your web-browsing tools, STOP and ask me to provide the website's HTML code/files).
2. **Analyze Local References:** Scan all screenshots provided in `<folder>`. Extract exact UI/UX value: layout structures, typographic hierarchy, spatial rhythm (padding/margins), and color distribution. 
3. **Review & Realign:** Do exactly TWO rounds of internal review comparing your planned architecture against the references and my stated goals. Fix any mismatches. Ensure the plan reflects a $100K+ design standard.
4. **Copywriting:** Do not use "lorem ipsum". Use your knowledge of DeepShield's capabilities (Deepfake detection, VLM/LLM explainability, metadata extraction, timeline analysis) to write custom, eye-catching, and highly persuasive copy that matches the premium theme. Swap in placeholder images via placehold.io where necessary.
5. **Build:** If no reference image exists for a specific view, design it from scratch with the highest possible craft.

### 3. TECHNICAL & STACK DIRECTIVES
* **Component Sourcing:** USE THE `21st.dev` MCP MAGIC SKILL to pull world-class, pre-built, high-end components (see Section 6 for exact targets). DO NOT build complex UI elements from scratch if a superior version exists on 21st.dev.
* **Base Components:** Use `shadcn/ui` as the foundational layer, but heavily customize them so they do not look generic.
* **Styling:** Use Tailwind CSS, but strictly **NEVER use the default Tailwind color palette**. Define and use custom colors derived from the references, or ask me to approve a specific graphite/indigo/teal/amber palette.
* **Animation Engine:** Use a combination of **GSAP** (for complex, scroll-driven timelines) and **Framer Motion** (for micro-interactions, spring physics, and layout transitions). 

### 4. ANIMATION & MOTION REQUIREMENTS
* **Scroll-Driven Excellence:** Create beautiful, world-class Apple-style scroll-driven animations for the landing page (e.g., text reveals, elements gliding into place on scroll, parallax backgrounds).
* **The Signature Element:** Implement the "3D Layer Animation" on the Analyze page. When a file is dropped, render 5-7 semi-transparent clones of the uploaded image stacked in 3D space (`transform: rotateX(60deg)`), with a glowing laser sweeping across them representing forensic passes.

### 5. UI/UX CRAFT & MICRO-AESTHETICS
* **Typography:** Pair a sophisticated, elegant Serif (for display/impact headers) with a hyper-clean Sans-serif (for UI and data density). Apply tight tracking (-0.02em to -0.04em) on display text for a premium feel.
* **Spatial & Surface Hierarchy:** Enforce a strict Z-axis layering system: `Base Canvas` > `Elevated (Cards)` > `Floating (Modals/Popovers/Nav)`. Verify all padding, spacing, and border-radii are mathematically consistent.
* **Interaction Fidelity:** EVERY single clickable or interactive element MUST have distinct, highly polished `hover`, `focus-visible`, and `active` states. Focus rings must be elegant (e.g., 2px offset brand-color rings).
* **Shadows:** Use multi-layered, soft, cinematic shadows, not flat CSS box-shadows. Combine shadows with backdrop-blur (`backdrop-filter: blur()`) for glassmorphism panels over mesh gradients.

### 6. SPECIFIC COMPONENT INSPIRATIONS & ASSETS
Use your web tools and MCP magic skill to pull the following inspirations. Treat these as your baseline. **Modify them subtly to perfectly fit the DeepShield dark mode/glassmorphism aesthetic.** If the MCP tool fails to pull the full code for any 21st.dev links, **stop and ask me for the full code.**
* **General UI/UX Inspiration:** https://specifyapp.com/?ref=landingfolio
* **Background:** Dotted surface -> https://21st.dev/community/components/efferd/dotted-surface/default
* **Hero Card:** Waitlist hero -> https://21st.dev/community/components/thanh/waitlist-hero/default
* **Hero Input / Shader UI:** AI input hero (great for overall UI and shader reference) -> https://21st.dev/community/components/erikx/ai-input-hero/default
* **Buttons:** Liquid glass & shiny -> https://21st.dev/community/components/aliimam/liquid-glass-button/default OR https://21st.dev/community/components/kokonutd/button-shiny/default
* **Navigation/Tabs:** Slide tabs -> https://21st.dev/community/components/thanh/slide-tabs/default
* **Auth Flow (Sign In/Up):** Sign-in flow 1 -> https://21st.dev/community/components/erikx/sign-in-flow-1/default
* **Loading States:** Tetris loader -> https://21st.dev/community/components/itaizeilig/tetris-loader/default
* **Result Cards / Dashboards:** Performance benchmark card -> https://21st.dev/community/components/kavikatiyar/performance-benchmark-card/default

*Note: You are not strictly limited to only these components. If you find a better-suited component on 21st.dev that matches the enterprise-forensic vibe, use it.*

Begin by confirming your understanding of these constraints, executing the 2-round reference analysis of `specifyapp.com` and `<folder>`, and presenting the structural plan for the redesign.