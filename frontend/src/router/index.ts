import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'Login',
            component: () => import('@/views/login/LoginView.vue'),
            meta: { requiresAuth: false }
        },
        {
            path: '/',
            component: () => import('@/layouts/MainLayout.vue'),
            meta: { requiresAuth: true },
            redirect: '/dashboard',
            children: [
                {
                    path: 'dashboard',
                    name: 'Dashboard',
                    component: () => import('@/views/dashboard/DashboardView.vue'),
                    meta: { title: '首页' }
                },
                {
                    path: 'system/users',
                    name: 'Users',
                    component: () => import('@/views/system/UserList.vue'),
                    meta: { title: '用户管理' }
                },
                {
                    path: 'system/departments',
                    name: 'Departments',
                    component: () => import('@/views/system/DepartmentList.vue'),
                    meta: { title: '部门管理' }
                },
                {
                    path: 'system/groups',
                    name: 'Groups',
                    component: () => import('@/views/system/GroupList.vue'),
                    meta: { title: '用户组管理' }
                },
                {
                    path: 'system/params',
                    name: 'SysParams',
                    component: () => import('@/views/system/ParamsList.vue'),
                    meta: { title: '系统参数' }
                },
                {
                    path: 'master/items',
                    name: 'Items',
                    component: () => import('@/views/master/ItemList.vue'),
                    meta: { title: '物料管理' }
                },
                {
                    path: 'master/customers',
                    name: 'Customers',
                    component: () => import('@/views/master/CustomerList.vue'),
                    meta: { title: '客户管理' }
                },
                {
                    path: 'master/eid',
                    name: 'EidList',
                    component: () => import('@/views/master/EidList.vue'),
                    meta: { title: 'EID 管理' }
                },
                {
                    path: 'master/assets',
                    name: 'Assets',
                    component: () => import('@/views/master/AssetList.vue'),
                    meta: { title: '资产台账' }
                }
            ]
        },
        {
            path: '/:pathMatch(.*)*',
            redirect: '/'
        }
    ]
})

router.beforeEach((to, _from, next) => {
    const token = localStorage.getItem('token')
    if (to.meta.requiresAuth !== false && !token) {
        next('/login')
    } else if (to.path === '/login' && token) {
        next('/')
    } else {
        next()
    }
})

export default router
