import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import type { Molecule3D, Atom } from '../types';
import { ELEMENT_COLORS, ELEMENT_RADII } from '../types';

function AtomSphere({ atom }: { atom: Atom }) {
  const color = ELEMENT_COLORS[atom.element] || '#FF69B4';
  const radius = ELEMENT_RADII[atom.element] || 0.3;

  return (
    <mesh position={[atom.x, atom.y, atom.z]}>
      <sphereGeometry args={[radius, 24, 24]} />
      <meshStandardMaterial color={color} roughness={0.3} metalness={0.1} />
    </mesh>
  );
}

function BondCylinder({ atom1, atom2, order }: { atom1: Atom; atom2: Atom; order: number }) {
  const start = new THREE.Vector3(atom1.x, atom1.y, atom1.z);
  const end = new THREE.Vector3(atom2.x, atom2.y, atom2.z);
  const mid = start.clone().add(end).multiplyScalar(0.5);
  const direction = end.clone().sub(start);
  const length = direction.length();

  const quaternion = useMemo(() => {
    const q = new THREE.Quaternion();
    q.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.clone().normalize());
    return q;
  }, [atom1, atom2]);

  const offsets = order === 1 ? [0] : order === 2 ? [-0.08, 0.08] : [-0.12, 0, 0.12];
  const perpendicular = useMemo(() => {
    const up = new THREE.Vector3(0, 0, 1);
    const perp = up.clone().cross(direction.clone().normalize());
    if (perp.length() < 0.01) perp.set(1, 0, 0);
    return perp.normalize();
  }, [atom1, atom2]);

  return (
    <>
      {offsets.map((offset, i) => {
        const pos = mid.clone().add(perpendicular.clone().multiplyScalar(offset));
        return (
          <mesh key={i} position={pos} quaternion={quaternion}>
            <cylinderGeometry args={[0.06, 0.06, length, 8]} />
            <meshStandardMaterial color="#666666" roughness={0.5} />
          </mesh>
        );
      })}
    </>
  );
}

function MoleculeScene({ molecule }: { molecule: Molecule3D }) {
  const groupRef = useRef<THREE.Group>(null);

  // Center the molecule
  const center = useMemo(() => {
    if (!molecule.atoms.length) return new THREE.Vector3();
    const avg = molecule.atoms.reduce(
      (acc, a) => ({ x: acc.x + a.x, y: acc.y + a.y, z: acc.z + a.z }),
      { x: 0, y: 0, z: 0 }
    );
    const n = molecule.atoms.length;
    return new THREE.Vector3(-avg.x / n, -avg.y / n, -avg.z / n);
  }, [molecule]);

  // Slow rotation
  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.15;
    }
  });

  if (!molecule.atoms.length) return null;

  return (
    <group ref={groupRef} position={center}>
      {molecule.atoms.map((atom, i) => (
        <AtomSphere key={`a-${i}`} atom={atom} />
      ))}
      {molecule.bonds.map((bond, i) => (
        <BondCylinder
          key={`b-${i}`}
          atom1={molecule.atoms[bond.atom1]}
          atom2={molecule.atoms[bond.atom2]}
          order={bond.order}
        />
      ))}
    </group>
  );
}

export default function MoleculeViewer({
  molecule,
  height = '400px',
  showLabel = true,
}: {
  molecule: Molecule3D | null;
  height?: string;
  showLabel?: boolean;
}) {
  if (!molecule || !molecule.atoms.length) {
    return (
      <div
        className="flex items-center justify-center rounded-lg"
        style={{ height, background: '#0d1420' }}
      >
        <p className="text-gray-500 text-sm">No molecule data</p>
      </div>
    );
  }

  return (
    <div className="relative rounded-lg overflow-hidden" style={{ height }}>
      <Canvas
        camera={{ position: [0, 0, 12], fov: 50 }}
        style={{ background: '#0d1420' }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={0.8} />
        <directionalLight position={[-5, -5, -3]} intensity={0.3} color="#6699ff" />
        <MoleculeScene molecule={molecule} />
        <OrbitControls enableDamping dampingFactor={0.1} />
      </Canvas>
      {showLabel && molecule.smiles && (
        <div className="absolute bottom-2 left-2 right-2 text-center">
          <span className="bg-black/60 text-xs text-gray-300 px-2 py-1 rounded font-mono">
            {molecule.smiles.length > 60
              ? molecule.smiles.slice(0, 57) + '...'
              : molecule.smiles}
          </span>
        </div>
      )}
    </div>
  );
}
