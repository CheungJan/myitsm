import request from './request'

// ---- 类型定义 ----

export interface ItemClassNode {
    class_cd: string
    class_nm: string
    childflg: string
    children: ItemClassNode[]
}

export interface ItemRecord {
    item_cd: string
    item_nm: string
    class_cd: string
    itemanm: string
    unit: string
    spec: string
    useflg: string
    [key: string]: unknown
}

export interface ItemsPage {
    items: ItemRecord[]
    total: number
}

export interface ItemQuery {
    page?: number | string
    per_page?: number | string
    class_cd?: string
    recursive?: boolean
    search?: string
}

// ---- 物料分类 ----

export function fetchItemClassTree() {
    return request.get<never, { data: ItemClassNode[] }>('/itemclasses/tree')
}

export function fetchItemClasses() {
    return request.get<never, { data: { class_cd: string; class_nm: string; parent_cd: string }[] }>('/itemclasses')
}

export function createItemClass(data: Record<string, string>) {
    return request.post<never, { data: ItemClassNode }>('/itemclasses', data)
}

export function updateItemClass(classCd: string, data: Record<string, string>) {
    return request.put<never, { data: ItemClassNode }>(`/itemclasses/${classCd}`, data)
}

export function deleteItemClass(classCd: string) {
    return request.delete<never, unknown>(`/itemclasses/${classCd}`)
}

// ---- 物料 CRUD ----

export function fetchItems(params?: ItemQuery) {
    return request.get<never, { data: ItemsPage }>('/items', { params })
}

export function createItem(data: Partial<ItemRecord>) {
    return request.post<never, { data: ItemRecord }>('/items', data)
}

export function updateItem(itemCd: string, data: Partial<ItemRecord>) {
    return request.put<never, { data: ItemRecord }>(`/items/${itemCd}`, data)
}

export function deleteItem(itemCd: string) {
    return request.delete<never, unknown>(`/items/${itemCd}`)
}

// ---- 客户分类 ----

export interface CustClassNode {
    class_cd: string
    class_nm: string
    childflg: string
    parent_cd: string
    useflg: string
    children: CustClassNode[]
}

export interface CustRecord {
    cust_cd: string
    cust_nm: string
    cust_card: string
    class_cd: string
    phone_no: string
    contactor: string
    address: string
    useflg: string
    cust_anm: string
    custrnm: string
    store_cd: string
    cust_brcd: string
    area_cd: string
    parentcd: string
    zipcd: string
    faxno: string
    taxno: string
    banknm: string
    bankaccno: string
    yj_money: string
    pos_n: string
    posstatus: string
    posstatus1: string
    ad_video: string
    opersystem: string
    data_base: string
    soft_edition: string
    systemcode: string
    card3g: string
    adr3g: string
    busi_typ: string
    ppt_code: string
    levels: string
    ordertype: string
    is_contract: string
    zf_type: string
    comm_mode: string
    customer_status: string
    opendate: string
    replacedate: string
    source_type: string
    preplan_id: string
    jl_contactor: string
    jl_phoneno: string
    area: string
    location: string
    s_status: string
    backup: string
    [key: string]: unknown
}

export interface CustPage {
    items: CustRecord[]
    total: number
}

export interface CustQuery {
    page?: number | string
    per_page?: number | string
    class_cd?: string
    search?: string
}

export function fetchCustClassTree() {
    return request.get<never, { data: CustClassNode[] }>('/custclasses/tree')
}

export function fetchCustClasses() {
    return request.get<never, { data: { class_cd: string; class_nm: string; parent_cd: string }[] }>('/custclasses')
}

export function createCustClass(data: Record<string, string>) {
    return request.post<never, { data: CustClassNode }>('/custclasses', data)
}

export function updateCustClass(classCd: string, data: Record<string, string>) {
    return request.put<never, { data: CustClassNode }>(`/custclasses/${classCd}`, data)
}

export function deleteCustClass(classCd: string) {
    return request.delete<never, unknown>(`/custclasses/${classCd}`)
}

// ---- 码表 ----

export function fetchSyscodes(codeTyp: string) {
    return request.get<never, { data: { code_cd: string; code_nm: string }[] }>('/syscodes', { params: { code_typ: codeTyp } })
}

export function fetchAreas() {
    return request.get<never, { data: { area_cd: string; area_nm: string; area_id: number; name: string }[] }>('/areas')
}

export function fetchCommodes() {
    return request.get<never, { data: { cmm_cd: string; cmm_nm: string }[] }>('/commodes')
}

export function fetchCountries() {
    return request.get<never, { data: { country_cd: string; country_nm: string }[] }>('/countries')
}

export function fetchProvinces() {
    return request.get<never, { data: { prvn_cd: string; prvn_nm: string }[] }>('/provinces')
}

export function fetchCities(prvnCd?: string) {
    return request.get<never, { data: { city_cd: string; city_nm: string }[] }>('/cities', { params: prvnCd ? { prvn_cd: prvnCd } : {} })
}

export function fetchTowns(cityCd?: string) {
    return request.get<never, { data: { town_cd: string; town_nm: string }[] }>('/towns', { params: cityCd ? { city_cd: cityCd } : {} })
}

// ---- 客户 ----

export function fetchCustomers(params?: CustQuery) {
    return request.get<never, { data: CustPage }>('/customers', { params })
}
export function createCustomer(data: Partial<CustRecord>) {
    return request.post<never, { data: CustRecord }>('/customers', data)
}
export function updateCustomer(custCd: string, data: Partial<CustRecord>) {
    return request.put<never, { data: CustRecord }>(`/customers/${custCd}`, data)
}
export function deleteCustomer(custCd: string) {
    return request.delete<never, unknown>(`/customers/${custCd}`)
}

// ---- 仓库 ----

export function fetchWarehouses(useflg?: string) {
    const params: Record<string, string> = {}
    if (useflg !== undefined && useflg !== '') {
        params.useflg = useflg
    }
    return request.get<never, { data: { whcd: string; whnm: string }[] }>('/warehouses', { params })
}

// ---- EID ----

export interface EidRecord {
    eid: string
    itemcd: string
    item_nm: string
    etyp: string
    whcd: string
    sflg: string
    new_old: string
    qcflg: string
    gendate: string
    prddate: string
    [key: string]: unknown
}

export interface EidPage {
    items: EidRecord[]
    total: number
}

export interface EidQuery {
    page?: number | string
    per_page?: number | string
    class_cd?: string
    search?: string
}

export function fetchEidTree() {
    return request.get<never, { data: ItemClassNode[] }>('/eid/tree')
}

export function fetchEidList(params?: EidQuery) {
    return request.get<never, { data: EidPage }>('/eid', { params })
}
export function createEid(data: Record<string, unknown>) {
    return request.post('/eid', data)
}
export function updateEid(itemcd: string, eidVal: string, data: Record<string, unknown>) {
    return request.put(`/eid/${itemcd}/${eidVal}`, data)
}
export function deleteEid(itemcd: string, eidVal: string) {
    return request.delete(`/eid/${itemcd}/${eidVal}`)
}

export function fetchEidTracks(itemcd: string, eid: string) {
    return request.get<never, { data: Record<string,unknown>[] }>(`/eid/${itemcd}/${eid}/tracks`)
}

// ---- 资产 ----

export function fetchAssets(params?: Record<string, string>) {
    return request.get('/assets', { params })
}
