/* ============================================================
   AGIChainAI — script.js
   Vanilla JavaScript only | No external libraries
   ============================================================ */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  /* ---------- 1. Sticky navbar (blur on scroll) ---------- */
  const navbar = document.getElementById("navbar");

  const handleNavbarScroll = () => {
    if (!navbar) return;
    navbar.classList.toggle("scrolled", window.scrollY > 40);
  };

  handleNavbarScroll();
  window.addEventListener("scroll", handleNavbarScroll, { passive: true });

  /* ---------- 2. Mobile menu ---------- */
  const navToggle = document.getElementById("navToggle");
  const navMenu = document.getElementById("navMenu");

  const closeMenu = () => {
    if (!navToggle || !navMenu) return;
    navToggle.classList.remove("open");
    navMenu.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  };

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", () => {
      const isOpen = navMenu.classList.toggle("open");
      navToggle.classList.toggle("open", isOpen);
      navToggle.setAttribute("aria-expanded", String(isOpen));
      document.body.style.overflow = isOpen ? "hidden" : "";
    });

    // Close menu when a link is clicked
    navMenu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", closeMenu);
    });

    // Close menu with Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeMenu();
    });
  }

  /* ---------- 3. Smooth scrolling for anchor links ---------- */
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const targetId = anchor.getAttribute("href");
      if (targetId === "#") return;
      const target = document.querySelector(targetId);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({
        behavior: prefersReducedMotion ? "auto" : "smooth",
        block: "start",
      });
    });
  });

  /* ---------- 4. Scroll reveal animations ---------- */
  const revealElements = document.querySelectorAll(".reveal");

  if ("IntersectionObserver" in window && revealElements.length) {
    const revealObserver = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    revealElements.forEach((el) => revealObserver.observe(el));
  } else {
    // Fallback: show everything
    revealElements.forEach((el) => el.classList.add("visible"));
  }

  /* ---------- 5. Counter animation ---------- */
  const counters = document.querySelectorAll("[data-count]");

  const animateCounter = (el) => {
    const target = parseInt(el.dataset.count, 10);
    if (Number.isNaN(target)) return;

    if (prefersReducedMotion) {
      el.textContent = target;
      return;
    }

    const duration = 1600;
    const start = performance.now();

    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(step);
    };

    requestAnimationFrame(step);
  };

  if ("IntersectionObserver" in window && counters.length) {
    const counterObserver = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.6 }
    );

    counters.forEach((el) => counterObserver.observe(el));
  } else {
    counters.forEach((el) => (el.textContent = el.dataset.count));
  }

  /* ---------- 6. Active navigation highlighting ---------- */
  const sections = document.querySelectorAll("main section[id]");
  const navLinks = document.querySelectorAll('.nav-link[href^="#"]');

  if ("IntersectionObserver" in window && sections.length && navLinks.length) {
    const sectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const id = entry.target.getAttribute("id");
          navLinks.forEach((link) => {
            link.classList.toggle(
              "active",
              link.getAttribute("href") === `#${id}`
            );
          });
        });
      },
      { rootMargin: "-40% 0px -55% 0px" }
    );

    sections.forEach((section) => sectionObserver.observe(section));
  }

  /* ---------- 7. Hero typing effect ---------- */
  const typingTarget = document.getElementById("typingTarget");

  if (typingTarget && !prefersReducedMotion) {
    const fullText = typingTarget.textContent.trim();
    typingTarget.textContent = "";

    const cursor = document.createElement("span");
    cursor.className = "typing-cursor";
    cursor.setAttribute("aria-hidden", "true");
    cursor.innerHTML = "&nbsp;";
    typingTarget.after(cursor);

    let index = 0;
    const typeSpeed = 90;

    const type = () => {
      if (index < fullText.length) {
        typingTarget.textContent += fullText.charAt(index);
        index += 1;
        setTimeout(type, typeSpeed);
      } else {
        // Remove cursor a moment after typing completes
        setTimeout(() => cursor.remove(), 2200);
      }
    };

    setTimeout(type, 500);
  }

  /* ---------- 8. Back-to-top button ---------- */
  const backToTop = document.getElementById("backToTop");

  if (backToTop) {
    const toggleBackToTop = () => {
      backToTop.classList.toggle("visible", window.scrollY > 600);
    };

    toggleBackToTop();
    window.addEventListener("scroll", toggleBackToTop, { passive: true });

    backToTop.addEventListener("click", () => {
      window.scrollTo({
        top: 0,
        behavior: prefersReducedMotion ? "auto" : "smooth",
      });
    });
  }

  /* ---------- 9. Particle animation (hero canvas) ---------- */
  const canvas = document.getElementById("particles");

  if (canvas && !prefersReducedMotion) {
    const ctx = canvas.getContext("2d");
    let particles = [];
    let animationId = null;
    let width = 0;
    let height = 0;

    const PARTICLE_COLOR = "0, 216, 255";
    const LINK_DISTANCE = 130;

    const resize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const createParticles = () => {
      const count = Math.min(Math.floor((width * height) / 16000), 90);
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: Math.random() * 1.8 + 0.6,
      }));
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw links between close particles
      for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.hypot(dx, dy);
          if (dist < LINK_DISTANCE) {
            const alpha = (1 - dist / LINK_DISTANCE) * 0.18;
            ctx.strokeStyle = `rgba(${PARTICLE_COLOR}, ${alpha})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw particles
      particles.forEach((p) => {
        ctx.fillStyle = `rgba(${PARTICLE_COLOR}, 0.7)`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();

        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;
      });

      animationId = requestAnimationFrame(draw);
    };

    const start = () => {
      resize();
      createParticles();
      if (animationId) cancelAnimationFrame(animationId);
      draw();
    };

    start();

    let resizeTimer;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(start, 200);
    });

    // Pause animation when the tab is hidden (performance)
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        if (animationId) cancelAnimationFrame(animationId);
        animationId = null;
      } else if (!animationId) {
        draw();
      }
    });
  }

  /* ---------- 10. FAQ accordion (used on pages/faq.html) ---------- */
  const accordionItems = document.querySelectorAll(".accordion-item");

  accordionItems.forEach((item) => {
    const header = item.querySelector(".accordion-header");
    const body = item.querySelector(".accordion-body");
    if (!header || !body) return;

    header.addEventListener("click", () => {
      const isOpen = item.classList.contains("open");

      // Close all items
      accordionItems.forEach((other) => {
        other.classList.remove("open");
        const otherBody = other.querySelector(".accordion-body");
        const otherHeader = other.querySelector(".accordion-header");
        if (otherBody) otherBody.style.maxHeight = null;
        if (otherHeader) otherHeader.setAttribute("aria-expanded", "false");
      });

      // Open clicked item (if it was closed)
      if (!isOpen) {
        item.classList.add("open");
        body.style.maxHeight = `${body.scrollHeight}px`;
        header.setAttribute("aria-expanded", "true");
      }
    });
  });

  /* ---------- 11. Theme loader (fade page in) ---------- */
  document.body.style.opacity = "0";
  document.body.style.transition = "opacity 0.5s ease";
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      document.body.style.opacity = "1";
    });
  });

  /* ---------- 12. Footer year auto-update ---------- */
  const yearTarget = document.querySelector("[data-year]");
  if (yearTarget) {
    yearTarget.textContent = new Date().getFullYear();
  }
});
