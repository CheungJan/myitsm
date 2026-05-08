import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
    baseURL: '/api/v1',
    timeout: 15000
})

request.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

request.interceptors.response.use(
    res => {
        const body = res.data
        if (body.code && body.code !== 200) {
            ElMessage.error(body.message || '操作失败')
            return Promise.reject(body)
        }
        return body
    },
    err => {
        if (err.response?.status === 401) {
            localStorage.removeItem('token')
            window.location.href = '/login'
        }
        const msg = err.response?.data?.message || '网络错误'
        ElMessage.error(msg)
        return Promise.reject(err)
    }
)

export default request
