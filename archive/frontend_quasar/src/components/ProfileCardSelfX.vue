<!--<template>-->
<!--  <q-card-->
<!--      class="col-auto"-->
<!--    >-->
<!--      <q-card-section-->
<!--        class="column justify-center items-center bg-teal-2 tw-h-32"-->
<!--      >-->
<!--        <ProfileImageSelf-->
<!--          editable-->
<!--          offset_classes="tw-top-8"-->
<!--          size="lg"-->
<!--        />-->
<!--      </q-card-section>-->
<!--      <q-card-section>-->
<!--        <div class="row justify-between q-pa-sm">-->
<!--          <div class="column text-h6 tw-text-gray-600 q-pr-xl">-->
<!--            username-->
<!--          </div>-->
<!--          <div class="column text-h6">-->
<!--            {{ user.username }}-->
<!--          </div>-->
<!--        </div>-->
<!--        <q-separator />-->
<!--        <div class="row justify-between q-pa-sm">-->
<!--          <div class="column text-h6 tw-text-gray-600 q-pr-xl">-->
<!--            email-->
<!--          </div>-->
<!--          <div class="column text-h6">-->
<!--            {{ user.email }}-->
<!--          </div>-->
<!--        </div>-->
<!--        <q-separator />-->
<!--        <div class="row justify-between q-pa-sm">-->
<!--          <div class="column text-h6 tw-text-gray-600 q-pr-xl">-->
<!--            teams-->
<!--          </div>-->
<!--          <div class="column">-->
<!--            <span v-for="role in user.teams" v-bind:key="role.id" class="tw-rounded q-pa-xs q-ma-xs tw-text-center tw-font-bold tw-border-2" :class="getColorForRole(role.name)">-->
<!--              {{ role.name }}-->
<!--            </span>-->
<!--          </div>-->
<!--        </div>-->
<!--        <q-separator />-->
<!--        <div class="row justify-between q-pa-sm">-->
<!--          <div class="column text-h6 tw-text-gray-600 q-pr-xl">-->
<!--            achievements-->
<!--          </div>-->
<!--        </div>-->
<!--&lt;!&ndash;        <div class="row justify-evenly">&ndash;&gt;-->
<!--&lt;!&ndash;          <AchievementIcon  :image="achiev.iconfile" :description="achiev.description" :count="achiev.count" v-for="achiev in LoggedInUserStore.GetUserAchievements.values()" v-bind:key="achiev.id" />&ndash;&gt;-->
<!--&lt;!&ndash;        </div>&ndash;&gt;-->
<!--      </q-card-section>-->
<!--    </q-card>-->
<!--</template>-->

<!--<script lang="ts">-->
<!--import { useLoggedInUserStore } from 'src/store/loggedinuser';-->
<!--import { useLoginStore} from 'src/store/login';-->
<!--import ProfileImageSelf from 'components/ProfileImageSelf.vue';-->
<!--import { computed, onMounted, ref } from 'vue';-->
<!--import {storeToRefs} from 'pinia';-->
<!--import { useRouter } from 'vue-router';-->

<!--export default {-->
<!--  name: 'ProfileCardSelf',-->
<!--  components: {-->
<!--    ProfileImageSelf-->
<!--  },-->

<!--  setup(){-->

<!--    const LoginStore = useLoginStore()-->
<!--    storeToRefs(LoginStore)-->

<!--    const LoggedInUserStore = useLoggedInUserStore()-->
<!--    storeToRefs(LoggedInUserStore)-->

<!--    const user = computed(() => LoggedInUserStore.user)-->

<!--    const router = useRouter()-->

<!--    let role_color_mapping = ref<{ [key: string]: string }>({-->
<!--      'Owners': 'bg-black text-white tw-border-gray-700',-->
<!--      'Supervisor': 'bg-pink-9 text-white tw-border-pink-600',-->
<!--    })-->

<!--    function getColorForRole(role: string){-->
<!--      if (role_color_mapping.value[role]){-->
<!--        return role_color_mapping.value[role]-->
<!--      }else{-->
<!--        return 'bg-amber-5 text-black tw-border-amber-400'-->
<!--      }-->
<!--    }-->

<!--    onMounted(async () => {-->
<!--      if (!LoginStore.isLoggedIn){-->
<!--        await router.push('/login')-->
<!--      }else{-->
<!--        await LoggedInUserStore.UpdateProfileInformation()-->
<!--      }-->
<!--    })-->

<!--    return {-->
<!--      user,-->
<!--      getColorForRole-->
<!--    }-->

<!--  }-->
<!--}-->
<!--</script>-->
