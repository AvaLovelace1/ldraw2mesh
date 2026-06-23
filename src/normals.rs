//! Edge-aware vertex normals.
//!
//! LDraw geometry arrives as welded triangles plus a list of "hard edges". We want
//! smooth shading across soft regions but crisp seams at hard edges. For each
//! original vertex we union its incident triangles that share a non-hard edge, then
//! emit one area-weighted normal per resulting smoothing group, duplicating the
//! vertex across groups. Triangle order is preserved so per-triangle attributes
//! (e.g. face colors) stay aligned.

use std::collections::{HashMap, HashSet};

use numpy::ndarray::{Array2, ArrayView2};

/// Normalize a 3-vector; returns a zero vector when the magnitude is ~0.
fn normalize(v: [f32; 3]) -> [f32; 3] {
    let n = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).sqrt();
    if n > 0.0 {
        [v[0] / n, v[1] / n, v[2] / n]
    } else {
        [0.0, 0.0, 0.0]
    }
}

/// Raw (area-weighted) triangle normal: cross(p1 - p0, p2 - p0).
fn raw_normal(p0: [f32; 3], p1: [f32; 3], p2: [f32; 3]) -> [f32; 3] {
    let a = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]];
    let b = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]];
    [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
}

/// Inline union-find over a small contiguous index set `0..n` (one per vertex).
struct UnionFind {
    parent: Vec<usize>,
}

impl UnionFind {
    fn new(n: usize) -> Self {
        Self { parent: (0..n).collect() }
    }

    fn find(&mut self, mut x: usize) -> usize {
        while self.parent[x] != x {
            self.parent[x] = self.parent[self.parent[x]]; // path halving
            x = self.parent[x];
        }
        x
    }

    fn union(&mut self, a: usize, b: usize) {
        let (ra, rb) = (self.find(a), self.find(b));
        if ra != rb {
            self.parent[ra] = rb;
        }
    }
}

/// Compute edge-aware vertex normals. See module docs for semantics.
pub fn edge_aware_normals(
    positions: ArrayView2<f32>,
    triangles: ArrayView2<u32>,
    hard_edges: ArrayView2<u32>,
) -> (Array2<f32>, Array2<f32>, Array2<u32>) {
    let n_tris = triangles.nrows();

    let pos = |v: u32| -> [f32; 3] {
        let r = positions.row(v as usize);
        [r[0], r[1], r[2]]
    };

    // Per-triangle vertex triples and raw (area-weighted) normals.
    let mut tri_verts: Vec<[u32; 3]> = Vec::with_capacity(n_tris);
    let mut raw_normals: Vec<[f32; 3]> = Vec::with_capacity(n_tris);
    for t in 0..n_tris {
        let row = triangles.row(t);
        let (a, b, c) = (row[0], row[1], row[2]);
        tri_verts.push([a, b, c]);
        raw_normals.push(raw_normal(pos(a), pos(b), pos(c)));
    }

    // Undirected hard-edge set keyed by (min, max).
    let mut hard: HashSet<(u32, u32)> = HashSet::new();
    for e in 0..hard_edges.nrows() {
        let row = hard_edges.row(e);
        let (a, b) = (row[0], row[1]);
        hard.insert((a.min(b), a.max(b)));
    }

    // Incident triangles per vertex, recording first-appearance order for determinism.
    let mut incident: HashMap<u32, Vec<usize>> = HashMap::new();
    let mut vertex_order: Vec<u32> = Vec::new();
    for t in 0..n_tris {
        for &v in &tri_verts[t] {
            incident
                .entry(v)
                .or_insert_with(|| {
                    vertex_order.push(v);
                    Vec::new()
                })
                .push(t);
        }
    }

    let mut out_positions: Vec<[f32; 3]> = Vec::new();
    let mut out_normals: Vec<[f32; 3]> = Vec::new();
    let mut corner_index: HashMap<(u32, usize), u32> = HashMap::new();

    for &v in &vertex_order {
        let tris = &incident[&v];
        let mut uf = UnionFind::new(tris.len());
        // Map triangle id -> local index into `tris`.
        let local: HashMap<usize, usize> =
            tris.iter().enumerate().map(|(i, &t)| (t, i)).collect();

        // Triangles sharing each edge (v, w).
        let mut edge_tris: HashMap<u32, Vec<usize>> = HashMap::new();
        for &t in tris {
            for &w in &tri_verts[t] {
                if w != v {
                    edge_tris.entry(w).or_default().push(t);
                }
            }
        }
        for (&w, ts) in &edge_tris {
            if hard.contains(&(v.min(w), v.max(w))) {
                continue;
            }
            for k in 1..ts.len() {
                uf.union(local[&ts[0]], local[&ts[k]]);
            }
        }

        // Group triangles by union-find root, preserving discovery order.
        let mut groups: HashMap<usize, Vec<usize>> = HashMap::new();
        let mut group_order: Vec<usize> = Vec::new();
        for &t in tris {
            let root = uf.find(local[&t]);
            groups
                .entry(root)
                .or_insert_with(|| {
                    group_order.push(root);
                    Vec::new()
                })
                .push(t);
        }

        for root in &group_order {
            let gts = &groups[root];
            let mut acc = [0.0f32; 3];
            for &t in gts {
                let rn = raw_normals[t];
                acc[0] += rn[0];
                acc[1] += rn[1];
                acc[2] += rn[2];
            }
            let idx = out_positions.len() as u32;
            out_positions.push(pos(v));
            out_normals.push(normalize(acc));
            for &t in gts {
                corner_index.insert((v, t), idx);
            }
        }
    }

    // Rebuild the triangle index buffer against the duplicated vertices.
    let mut out_tris = Array2::<u32>::zeros((n_tris, 3));
    for t in 0..n_tris {
        for (j, &v) in tri_verts[t].iter().enumerate() {
            out_tris[[t, j]] = corner_index[&(v, t)];
        }
    }

    let n_out = out_positions.len();
    let mut pos_arr = Array2::<f32>::zeros((n_out, 3));
    let mut nrm_arr = Array2::<f32>::zeros((n_out, 3));
    for i in 0..n_out {
        for j in 0..3 {
            pos_arr[[i, j]] = out_positions[i][j];
            nrm_arr[[i, j]] = out_normals[i][j];
        }
    }

    (pos_arr, nrm_arr, out_tris)
}
