<script lang="ts">
  /**
   * CardParticles - 3D particles inside card (inspired by Beatcatalogue ContentDetail).
   * 
   * Features:
   * - Falling droplets with Three.js
   * - Cyan/Magenta colors → Kidyland Blue/Green
   * - Auto-reset when droplets reach bottom
   * - Desktop only for performance
   */
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  
  let particleContainer: HTMLDivElement;
  let isMobile = false;
  
  onMount(async () => {
    if (!browser) return;
    
    // Detectar móvil
    isMobile = window.innerWidth < 768 || 
               /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               ('ontouchstart' in window);
    
    // Solo ejecutar WebGL en desktop
    if (isMobile) return;
    
    try {
      const THREE = await import("three");
      
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
      camera.position.z = 30;
      
      const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false });
      const rect = particleContainer.getBoundingClientRect();
      renderer.setSize(rect.width, rect.height);
      particleContainer.appendChild(renderer.domElement);
      
      const count = 15;
      const droplets: THREE.Mesh[] = [];
      
      for (let i = 0; i < count; i++) {
        const geometry = new THREE.SphereGeometry(2, 8, 6);
        
        // Deform sphere to make droplet shape
        const positions = geometry.attributes.position;
        for (let j = 0; j < positions.count; j++) {
          const y = positions.getY(j);
          if (y > 0) positions.setY(j, y * 1.5);
          if (y < 0) positions.setY(j, y * 0.8);
        }
        
        // Kidyland colors instead of cyan/magenta
        const material = new THREE.MeshPhongMaterial({
          color: Math.random() > 0.5 ? 0x0093f7 : 0x3dad09, // Kidyland blue/green
          transparent: true,
          opacity: 0.3,
          shininess: 100
        });
        
        const droplet = new THREE.Mesh(geometry, material);
        droplet.position.set(
          (Math.random() - 0.5) * 80,
          Math.random() * 80 - 40,
          (Math.random() - 0.5) * 40
        );
        
        droplet.userData.speed = Math.random() * 0.02 + 0.01;
        droplet.userData.rotationSpeed = (Math.random() - 0.5) * 0.02;
        
        scene.add(droplet);
        droplets.push(droplet);
      }
      
      // Lights
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
      scene.add(ambientLight);
      
      const pointLight = new THREE.PointLight(0x0093f7, 1); // Kidyland blue
      pointLight.position.set(10, 10, 20);
      scene.add(pointLight);
      
      function animate() {
        requestAnimationFrame(animate);
        
        droplets.forEach((droplet) => {
          droplet.position.y -= droplet.userData.speed;
          droplet.rotation.z += droplet.userData.rotationSpeed;
          
          // Reset when droplet reaches bottom
          if (droplet.position.y < -40) {
            droplet.position.y = 40;
            droplet.position.x = (Math.random() - 0.5) * 80;
          }
        });
        
        renderer.render(scene, camera);
      }
      
      animate();
      
      return () => {
        renderer.dispose();
        if (particleContainer && renderer.domElement) {
          particleContainer.removeChild(renderer.domElement);
        }
      };
    } catch (error) {
      console.warn("CardParticles WebGL failed:", error);
    }
  });
</script>

{#if !isMobile}
  <div
    bind:this={particleContainer}
    class="card-particles"
  ></div>
{/if}

<style>
  .card-particles {
    position: absolute;
    inset: 0;
    pointer-events: none;
    opacity: 0.25;
    border-radius: inherit;
    overflow: hidden;
  }
</style>



