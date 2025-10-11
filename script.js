
    // ---- Mobile nav toggle ----
    const navToggle = document.getElementById('navToggle');
    const primaryNav = document.getElementById('primaryNav');
    navToggle && navToggle.addEventListener('click', ()=>{
      const isOpen = primaryNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Smooth scroll helper
    function scrollToSection(sel){
      const el = document.querySelector(sel);
      if(!el) return;
      el.scrollIntoView({behavior:'smooth', block:'start'});
    }

    // ---- IntersectionObserver to animate on scroll ----
    const io = new IntersectionObserver((entries)=>{
      entries.forEach(e=>{
        if(e.isIntersecting){
          e.target.classList.add('in-view');
          io.unobserve(e.target);
        }
      });
    }, {threshold: .15});

    document.querySelectorAll('.animate-on-scroll, .fade-in-up').forEach(el=> io.observe(el));

    // ---- Like / Dislike / Comment demo ----
    const likeBtn = document.getElementById('likeBtn');
    const dislikeBtn = document.getElementById('dislikeBtn');
    const likeCount = document.getElementById('likeCount');
    const dislikeCount = document.getElementById('dislikeCount');
    const commentInp = document.getElementById('commentInp');
    const addComment = document.getElementById('addComment');
    const commentsList = document.getElementById('commentsList');

    let likes = 0, dislikes = 0;
    likeBtn && likeBtn.addEventListener('click', ()=>{
      likes++;
      likeCount.textContent = likes;
      likeBtn.classList.add('pulse');
      setTimeout(()=> likeBtn.classList.remove('pulse'), 700);
    });
    dislikeBtn && dislikeBtn.addEventListener('click', ()=>{
      dislikes++;
      dislikeCount.textContent = dislikes;
      dislikeBtn.classList.add('pulse');
      setTimeout(()=> dislikeBtn.classList.remove('pulse'), 700);
    });

    addComment && addComment.addEventListener('click', ()=>{
      const text = (commentInp.value|| '').trim();
      if(!text) return;
      const div = document.createElement('div');
      div.className = 'comment';
      div.textContent = text;
      commentsList.prepend(div);
      commentInp.value = '';
    });

    // ---- Check status demo (simulated) ----
    const checkBtn = document.getElementById('checkStatusBtn');
    const statusResult = document.getElementById('statusResult');
    checkBtn && checkBtn.addEventListener('click', ()=>{
      const id = document.getElementById('complaintId').value.trim();
      if(!id){
        statusResult.style.display = 'block';
        statusResult.textContent = 'Please enter a valid complaint ID to continue.';
        statusResult.style.background = '#ffe9e9';
        return;
      }

      // simulated statuses
      const statuses = ['Received — awaiting verification','Verified — assigned to department','In Progress — field team notified','Escalated','Resolved — awaiting confirmation'];
      const idx = Math.floor(Math.random()*statuses.length);
      statusResult.style.display = 'block';
      statusResult.style.background = 'linear-gradient(90deg,#eff9ff,#f8fff6)';
      statusResult.innerHTML = `<strong>${id}</strong><div style="margin-top:.5rem;">Status: <em>${statuses[idx]}</em></div>`;
    });

    // Close mobile nav when clicking outside (nice small UX touch)
    document.addEventListener('click', (e)=>{
      if(!primaryNav || !navToggle) return;
      if(primaryNav.classList.contains('open') && !primaryNav.contains(e.target) && !navToggle.contains(e.target)){
        primaryNav.classList.remove('open');
        navToggle.setAttribute('aria-expanded','false');
      }
    });
// For logout button
