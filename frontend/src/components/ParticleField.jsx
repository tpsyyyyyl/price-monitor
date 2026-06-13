import { useEffect, useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

const GRID = 80 // 80 x 80 = 6400 points
const SPREAD = 60 // world units the plane spans on X and Z

function Wave() {
  const pointsRef = useRef(null)
  const geomRef = useRef(null)

  // Static base positions (XZ grid) + the live position array we mutate.
  const { positions, base } = useMemo(() => {
    const count = GRID * GRID
    const positions = new Float32Array(count * 3)
    const base = new Float32Array(count * 2) // x, z per point
    let i = 0
    for (let ix = 0; ix < GRID; ix++) {
      for (let iz = 0; iz < GRID; iz++) {
        const x = (ix / (GRID - 1) - 0.5) * SPREAD
        const z = (iz / (GRID - 1) - 0.5) * SPREAD
        base[i * 2] = x
        base[i * 2 + 1] = z
        positions[i * 3] = x
        positions[i * 3 + 1] = 0
        positions[i * 3 + 2] = z
        i++
      }
    }
    return { positions, base }
  }, [])

  const reduced = useMemo(
    () =>
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    []
  )

  // Mutable runtime state kept in refs so it survives re-renders without redraw.
  const intensity = useRef(0) // current, lerped
  const target = useRef(0) // driven by pm:intensity events
  const scroll = useRef({ y: 0, vel: 0 })

  useEffect(() => {
    function onIntensity(e) {
      const count = Number(e.detail) || 0
      target.current = Math.min(count / 30, 1)
    }
    let lastY = window.scrollY
    function onScroll() {
      const y = window.scrollY
      scroll.current.vel = y - lastY
      scroll.current.y = y
      lastY = y
    }
    window.addEventListener('pm:intensity', onIntensity)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('pm:intensity', onIntensity)
      window.removeEventListener('scroll', onScroll)
    }
  }, [])

  // Compute the wave for a given time; shared by animated + static paths.
  function applyWave(t) {
    const k = intensity.current
    const amp = 0.8 + k * 5.5 // calm base, tall on results
    const scrollPhase = scroll.current.y * 0.002
    const turb = scroll.current.vel * 0.05
    const pos = positions
    const b = base
    for (let i = 0; i < GRID * GRID; i++) {
      const x = b[i * 2]
      const z = b[i * 2 + 1]
      const y =
        Math.sin(x * 0.18 + t + scrollPhase) * amp +
        Math.sin(z * 0.22 - t * 0.8 + scrollPhase) * amp * 0.7 +
        Math.sin((x + z) * 0.1 + t * 0.5 + turb) * amp * 0.5
      pos[i * 3 + 1] = y
    }
    geomRef.current.attributes.position.needsUpdate = true
  }

  useFrame((state) => {
    if (reduced) return
    // Ease intensity toward its target.
    intensity.current += (target.current - intensity.current) * 0.04
    // Decay scroll velocity so turbulence settles after scrolling stops.
    scroll.current.vel *= 0.9

    const speed = 0.25 + intensity.current * 1.4
    const t = state.clock.elapsedTime * speed
    applyWave(t)

    // Slow whole-field rotation, nudged by scroll position.
    if (pointsRef.current) {
      pointsRef.current.rotation.y =
        scroll.current.y * 0.0006 + state.clock.elapsedTime * 0.02
    }
  })

  // Reduced-motion: render the wave once, statically.
  useEffect(() => {
    if (reduced && geomRef.current) applyWave(0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reduced])

  return (
    <points ref={pointsRef}>
      <bufferGeometry ref={geomRef}>
        <bufferAttribute
          attach="attributes-position"
          count={GRID * GRID}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.18}
        color="#6366f1"
        transparent
        opacity={0.85}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  )
}

export default function ParticleField() {
  return (
    <Canvas
      style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }}
      camera={{ position: [0, 14, 26], fov: 60 }}
      gl={{ antialias: true, alpha: true }}
      dpr={[1, 2]}
    >
      <Wave />
    </Canvas>
  )
}
