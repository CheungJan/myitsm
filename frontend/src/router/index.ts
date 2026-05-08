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
