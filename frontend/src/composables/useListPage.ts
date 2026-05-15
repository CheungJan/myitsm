import { ref, watch, onMounted, type Ref } from 'vue'
import { ElMessage } from 'element-plus'

interface PageData<T> { items: T[]; total: number }

export function useListPage<T>(
  fetcher: (params: Record<string, string>) => Promise<{ data: PageData<T> }>,
  options?: { perPage?: number }
) {
  const items = ref<T[]>([]) as Ref<T[]>
  const loading = ref(false)
  const page = ref(1)
  const perPage = ref(options?.perPage || 20)
  const total = ref(0)
  const searchParams = ref<Record<string, string>>({})

  watch(page, () => load())
  watch(perPage, () => { page.value = 1; load() })

  async function load() {
    loading.value = true
    try {
      const params: Record<string, string> = {
        page: String(page.value),
        per_page: String(perPage.value),
        ...searchParams.value,
      }
      const res = await fetcher(params)
      items.value = (res.data as PageData<T>).items || []
      total.value = (res.data as PageData<T>).total || 0
    } catch (e: unknown) {
      const msg = (e as any)?.response?.data?.message || '加载失败'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  }

  function onSearch(params?: Record<string, string>) {
    if (params) searchParams.value = { ...params }
    page.value = 1
    load()
  }

  onMounted(() => load())

  return { items, loading, page, perPage, total, load, onSearch, searchParams }
}
