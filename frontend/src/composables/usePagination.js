import { ref, computed, isRef } from 'vue'

export function usePagination(fetchFn, options = {}) {
  const defaultPerPage = typeof options === 'number' ? options : (options.defaultPerPage || 15)
  const extraParams = (typeof options === 'object' && options.extraParams) || ref({})

  const page = ref(1)
  const perPage = ref(defaultPerPage)
  const total = ref(0)
  const totalPages = computed(() => Math.ceil(total.value / perPage.value) || 1)
  const search = ref('')
  const items = ref([])
  const loading = ref(false)

  async function load(silent = false) {
    if (!silent) loading.value = true
    try {
      const extra = isRef(extraParams) ? extraParams.value : extraParams
      const res = await fetchFn({
        page: page.value,
        per_page: perPage.value,
        filename: search.value,
        ...extra,
      })
      items.value = res.data.items || []
      total.value = res.data.total || 0
    } finally {
      if (!silent) loading.value = false
    }
  }

  function handlePageChange(newPage) {
    page.value = newPage
    return load()
  }

  function handleSearch() {
    page.value = 1
    return load()
  }

  return {
    page,
    perPage,
    total,
    totalPages,
    search,
    items,
    loading,
    load,
    handlePageChange,
    handleSearch,
    extraParams,
  }
}
