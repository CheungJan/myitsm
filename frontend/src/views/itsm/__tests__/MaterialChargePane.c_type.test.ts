/**
 * V3 前端测试：MaterialChargePane c_type 推荐规则
 *
 * 验证 1a C8：工单创建时按资产属性+权益自动推荐 c_type。
 * 对齐文档 §3.5.4 和 1a阶段实施计划.md V3。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

// 模拟 API 返回
const mockResolveEntitlement = vi.fn()
const mockFetchItemPrice = vi.fn()
const mockFetchAccessories = vi.fn().mockResolvedValue({ data: [] })
const mockUseDict = vi.fn().mockReturnValue({
  dictOptions: { value: [] },
  dictLabel: vi.fn().mockReturnValue(''),
})

vi.mock('@/api/itsm', () => ({
  resolveEntitlement: (...args: any[]) => mockResolveEntitlement(...args),
  fetchItemPrice: (...args: any[]) => mockFetchItemPrice(...args),
  fetchAccessories: (...args: any[]) => mockFetchAccessories(...args),
  createAccessories: vi.fn(),
  updateAccessories: vi.fn(),
  fetchNewAccessoriesCandidates: vi.fn().mockResolvedValue({ data: [] }),
  fetchOldAccessoriesCandidates: vi.fn().mockResolvedValue({ data: [] }),
}))

vi.mock('@/composables/useDict', () => ({
  useDict: () => mockUseDict(),
}))

// 模拟 Element Plus 组件
vi.mock('element-plus', () => ({}))
vi.mock('@element-plus/icons-vue', () => ({ Search: {} }))

import MaterialChargePane from '../MaterialChargePane.vue'

describe('V3: c_type 推荐规则', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseDict.mockReturnValue({
      dictOptions: { value: [] },
      dictLabel: vi.fn().mockReturnValue(''),
    })
  })

  it('商用电子设备 → 推荐 c_type=1（配件更换免费）', async () => {
    mockResolveEntitlement.mockResolvedValue({
      data: {
        entitlement: { free: true, reason: '商用电子（默认免费）' },
        recommended_c_type: '1',
        recommended_sr: '01',
        asset_owner: '01',
      },
    })

    const wrapper = mount(MaterialChargePane, {
      props: { maintenanceId: '', storeId: 'S001', engineerId: '' },
      global: { stubs: { ItsmSubTablePane: { template: '<div/>' }, FaultCodeCascader: { template: '<div/>' } } },
    })

    const vm = wrapper.vm as any
    const form = { device_id: 'EID001', c_type: '' }
    await vm.onFormInit(form)
    await nextTick()

    expect(mockResolveEntitlement).toHaveBeenCalledWith('EID001', 'S001')
    expect(form.c_type).toBe('1')
  })

  it('门店资产保内 → 推荐 c_type=1（免费更换）', async () => {
    mockResolveEntitlement.mockResolvedValue({
      data: {
        entitlement: { free: true, reason: '保内' },
        recommended_c_type: '1',
        recommended_sr: '01',
        asset_owner: '03',
      },
    })

    const wrapper = mount(MaterialChargePane, {
      props: { maintenanceId: '', storeId: 'S003', engineerId: '' },
      global: { stubs: { ItsmSubTablePane: { template: '<div/>' }, FaultCodeCascader: { template: '<div/>' } } },
    })

    const vm = wrapper.vm as any
    const form = { device_id: 'EID003', c_type: '' }
    await vm.onFormInit(form)
    await nextTick()

    expect(form.c_type).toBe('1')
  })

  it('门店资产过保 → 推荐 c_type=2（购买）', async () => {
    mockResolveEntitlement.mockResolvedValue({
      data: {
        entitlement: { free: false, reason: '过保' },
        recommended_c_type: '2',
        recommended_sr: '01',
        asset_owner: '03',
      },
    })

    const wrapper = mount(MaterialChargePane, {
      props: { maintenanceId: '', storeId: 'S003', engineerId: '' },
      global: { stubs: { ItsmSubTablePane: { template: '<div/>' }, FaultCodeCascader: { template: '<div/>' } } },
    })

    const vm = wrapper.vm as any
    const form = { device_id: 'EID003', c_type: '' }
    await vm.onFormInit(form)
    await nextTick()

    expect(form.c_type).toBe('2')
  })

  it('无设备 → 不触发推荐', async () => {
    const wrapper = mount(MaterialChargePane, {
      props: { maintenanceId: '', storeId: 'S001', engineerId: '' },
      global: { stubs: { ItsmSubTablePane: { template: '<div/>' }, FaultCodeCascader: { template: '<div/>' } } },
    })

    const vm = wrapper.vm as any
    const form = { device_id: '', c_type: '' }
    await vm.onFormInit(form)
    await nextTick()

    // 无 device_id 不调用 API
    expect(mockResolveEntitlement).not.toHaveBeenCalled()
    expect(form.c_type).toBe('')
  })

  it('已手动选择 c_type → 不触发推荐', async () => {
    const wrapper = mount(MaterialChargePane, {
      props: { maintenanceId: '', storeId: 'S003', engineerId: '' },
      global: { stubs: { ItsmSubTablePane: { template: '<div/>' }, FaultCodeCascader: { template: '<div/>' } } },
    })

    const vm = wrapper.vm as any
    const form = { device_id: 'EID003', c_type: '3' }  // 已选手工服务费
    await vm.onFormInit(form)
    await nextTick()

    // 已有 c_type 时不调用 API
    expect(mockResolveEntitlement).not.toHaveBeenCalled()
    expect(form.c_type).toBe('3')  // 保持原值
  })

  it('API 失败 → 静默失败，不影响表单', async () => {
    mockResolveEntitlement.mockRejectedValue(new Error('网络错误'))

    const wrapper = mount(MaterialChargePane, {
      props: { maintenanceId: '', storeId: 'S001', engineerId: '' },
      global: { stubs: { ItsmSubTablePane: { template: '<div/>' }, FaultCodeCascader: { template: '<div/>' } } },
    })

    const vm = wrapper.vm as any
    const form = { device_id: 'EID001', c_type: '' }
    await vm.onFormInit(form)
    await nextTick()

    // 失败不抛异常，c_type 保持空
    expect(form.c_type).toBe('')
  })
})
