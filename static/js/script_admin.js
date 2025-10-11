// Sidebar toggle
const menuToggle = document.getElementById("menu-toggle");
const sidebar = document.querySelector(".sidebar");

if (menuToggle) {
  menuToggle.addEventListener("click", () => {
    sidebar.classList.toggle("active");
  });
}


// Highlight active link
document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", function () {
    document.querySelectorAll(".nav-link").forEach((l) =>
      l.classList.remove("active")
    );
    this.classList.add("active");
  });
});

// Animated counters
function animateValue(id, start, end, duration) {
  const obj = document.getElementById(id);
  let startTime = null;

  function step(timestamp) {
    if (!startTime) startTime = timestamp;
    let progress = Math.min((timestamp - startTime) / duration, 1);
    obj.innerText = Math.floor(progress * (end - start) + start);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// Trigger counters only when visible
function runCounterOnVisible(id, end, duration) {
  const element = document.getElementById(id);
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        animateValue(id, 0, end, duration);
        observer.unobserve(element);
      }
    },
    { threshold: 0.5 }
  );
  observer.observe(element);
}

runCounterOnVisible("stat1", 24, 1200);
runCounterOnVisible("stat2", 12, 1400);
runCounterOnVisible("stat3", 36, 1600);





// Dummy recent issues data (replace with backend API later)
const recentIssues = [
    { id: 1, citizen: "Amit Sharma", issue: "Pothole near market road", status: "Pending", date: "2025-09-06" },
    { id: 2, citizen: "Neha Patel", issue: "Streetlight not working", status: "In Progress", date: "2025-09-07" },
    { id: 3, citizen: "Ravi Kumar", issue: "Garbage collection delay", status: "Resolved", date: "2025-09-05" },
    { id: 4, citizen: "Pooja Verma", issue: "Water supply issue", status: "Pending", date: "2025-09-08" }
  ];
  
  function loadRecentIssues() {
    const tbody = document.getElementById("recent-issues-body");
    tbody.innerHTML = "";
  
    recentIssues.forEach((issue, index) => {
      const row = document.createElement("tr");
  
      row.innerHTML = `
        <th scope="row">${index + 1}</th>
        <td>${issue.citizen}</td>
        <td>${issue.issue}</td>
        <td>
          <span class="badge ${
            issue.status === "Resolved" ? "bg-success" :
            issue.status === "In Progress" ? "bg-warning text-dark" : "bg-danger"
          }">${issue.status}</span>
        </td>
        <td>${issue.date}</td>
      `;
      tbody.appendChild(row);
    });
  }
  
  document.addEventListener("DOMContentLoaded", loadRecentIssues);
  
  