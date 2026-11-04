/*
 * Product API calls. Each function wraps one backend endpoint and returns the
 * response data, so pages/components don't repeat URL strings.
 */
import api from './axios'

// Build the query params object for the product list from (possibly empty) UI
// values, dropping anything blank so we don't send ?search=&category= noise.
// Pure function -> unit tested in products.test.js.
export function buildProductQuery({ search, category, ordering, page } = {}) {
  const params = {}
  if (search) params.search = search
  if (category) params.category = category
  if (ordering) params.ordering = ordering
  if (page && page > 1) params.page = page
  return params
}

// List products. `params` maps to query string: { search, category, ordering, page }.
export async function fetchProducts(params = {}) {
  const { data } = await api.get('/products/', { params })
  return data   // { count, next, previous, results: [...] }
}

// Fetch a single product by its slug.
export async function fetchProduct(slug) {
  const { data } = await api.get(`/products/${slug}/`)
  return data
}

// List all categories.
export async function fetchCategories() {
  const { data } = await api.get('/categories/')
  return data   // { count, results: [...] } (paginated)
}
