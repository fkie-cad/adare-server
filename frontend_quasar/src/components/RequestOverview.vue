<template>
  <div
    v-if="request"
    class="tw-w-full"
  >
    <q-card class="q-ma-lg">
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">
            <RequestItemIcon :item="request.objective_name" size="1.25em" :tooltip=false color="secondary"/> request object
          </div>
          <div class="col tw-text-right">uuid</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{ request.object.name }}</div>
          <div class="col tw-text-right">{{ request.uuid }}</div>
        </div>
      </q-card-section>
      <q-separator />
    </q-card>
  </div>


</template>


<script lang="ts">
import {onMounted, ref} from 'vue'
import { Request } from 'src/datatypes/scenario'
import axios from 'axios';
import RequestItemIcon from 'components/global/RequestItemIcon.vue';
import ProfileImage from 'components/ProfileImage.vue';
import {status_color_mapping} from 'src/constants/mappings';
import { useRouter } from 'vue-router';
import { useLoggedInUserStore } from 'src/stores/loggedinuser';
import { storeToRefs } from 'pinia';


export default {
  name: 'RequestOverview',

  components: {RequestItemIcon},

  props: {
    uuid: {
      type: String,
      required: true,
    },
  },

  setup(props) {

    const router = useRouter()
    const LoggedInUserStore = useLoggedInUserStore()
    storeToRefs(LoggedInUserStore)

    const request = ref<Request | null>(null)
    const status_color = ref<string>('')

    const supervisors = ref<string[]>([])
    const selected_supervisor = ref<string>('')

    async function LoadRequest() {
      await axios.get('http://localhost:8000/api/request/request_'+props.uuid+'/').then(
        (response) => {
          request.value = response.data
        }
      )
    }

    function NavigateToCategory() {
      if (request.value){
        router.push('/'+ request.value.category.type + 'details/'+request.value.category.category.uuid)
      }
    }

    onMounted(async () => {
      await LoadRequest()
      if (request.value) {
        status_color.value = 'bg-' + status_color_mapping[request.value.status.name as keyof typeof status_color_mapping]
      }
    })

    return {
      request,
      status_color,
      NavigateToCategory,
      LoggedInUserStore,
      supervisors,
      selected_supervisor,
    }
  }
}

</script>

