  
  if (localStorage.getItem('ignoreMe') !== 'true') {
    
    // Agar 'ignoreMe' nahi milta, tabhi Analytics load hoga
    var script = document.createElement('script');
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=G-ZRZ11QPD5B";
    document.head.appendChild(script);

    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-ZRZ11QPD5B');
    
    console.log("Analytics is active for this session.");
  } else {
    // Agar 'ignoreMe' mil gaya, toh console mein message dikhega (sirf testing ke liye)
    console.log("Admin detected: Analytics is disabled.");
  }
    
    function toggleMenu() {
        const nav = document.getElementById('nav');
        nav.classList.toggle('active');
        // Prevent scrolling when menu is open
        document.body.style.overflow = nav.classList.contains('active') ? 'hidden' : 'auto';
    }
    // Close menu when clicking links
    document.querySelectorAll('#nav a').forEach(link => {
        link.onclick = () => {
            document.getElementById('nav').classList.remove('active');
            document.body.style.overflow = 'auto';
        };
    });
