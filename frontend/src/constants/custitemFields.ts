// 供应商商品关联 - 周期字段统一配置
// 用于 ItemList "供应商" tab 和 SupplierList "供应商品" 弹窗

export interface CycleFieldConfig {
  key: string
  label: string
  tooltip: string
  min: number
  controlsPosition: 'right'
}

export const CYCLE_FIELDS_CONFIG: CycleFieldConfig[] = [
  {
    key: 'delivercycle',
    label: '配送周期(天)',
    tooltip: '请填写该供应商实际配送所需天数',
    min: 0,
    controlsPosition: 'right'
  },
  {
    key: 'servicecycle',
    label: '服务周期(天)',
    tooltip: '请填写该供应商实际服务响应天数',
    min: 0,
    controlsPosition: 'right'
  },
  {
    key: 'guaranteeperiod',
    label: '保修期(天)',
    tooltip: '请填写该供应商提供的保修天数',
    min: 0,
    controlsPosition: 'right'
  }
]
