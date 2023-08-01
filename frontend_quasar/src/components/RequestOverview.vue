<template>
  <div
    v-if="request"
    class="tw-w-full"
  >
    <q-card class="q-ma-lg">
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">
            <RequestItemIcon :item="request.category.type" size="1.25em" :tooltip=false color="secondary"/> request name
          </div>
          <div class="col tw-text-right">uuid</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{ request.title }}</div>
          <div class="col tw-text-right">{{ request.uuid }}</div>
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section class="row">
        <div
          class="col q-pa-md"
        >
          <q-card>
            <q-card-section class="q-pa-sm bg-primary text-white">
              <div class="tw-text-center tw-text-2xl">
                 {{ request.category.type.charAt(0).toUpperCase() + request.category.type.slice(1) }} Request Metadata
              </div>
            </q-card-section>
            <q-separator/>
            <q-markup-table
              dense
            >
              <tbody>
                <tr>
                  <td class="tw-text-left">status</td>
                  <td class="tw-text-right">
                    {{ request.status.name }} <StatusIcon :status="request.status.name" size="2.5em" :tooltip=false />
                  </td>
                </tr>
                <tr>
                  <td class="tw-text-left">requestor</td>
                  <td>
                    <div class="tw-float-right">
                      <div class="tw-w-fit tw-h-fit q-py-md">
                        <div class="row tw-border-solid tw-rounded tw-border-2 tw-border-slate-400 q-pa-sm">
                          <div class="q-px-md tw-self-center">
                            {{ request.requestor }}
                          </div>
                          <ProfileImage
                            :username="request.requestor"
                            tooltip="true"
                            linktoprofile="true"
                          />
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td class="tw-text-left">supervisor</td>
                  <td>
                    <div class="tw-float-right">
                      <div class="tw-w-fit tw-h-fit q-py-md">
                        <div
                          class="row tw-border-solid tw-rounded tw-border-2 tw-border-slate-400 q-pa-sm"
                          v-if="request.supervisor"
                        >
                          <div class="q-px-md tw-self-center">
                            {{ request.supervisor }}
                          </div>
                          <ProfileImage
                            :username="request.supervisor"
                            tooltip="true"
                            linktoprofile="true"
                          />
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td class="tw-text-left">assigned by</td>
                  <td>
                    <div class="tw-float-right">
                      <div class="tw-w-fit tw-h-fit q-py-md">
                        <div
                          class="row tw-border-solid tw-rounded tw-border-2 tw-border-slate-400 q-pa-sm"
                          v-if="request.supervisor_assigned_by"
                        >
                          <div class="q-px-md tw-self-center">
                            {{ request.supervisor_assigned_by }}
                          </div>
                          <ProfileImage
                            :username="request.supervisor_assigned_by"
                            tooltip="true"
                            linktoprofile="true"
                          />
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </q-markup-table>
          </q-card>
        </div>
        <div
          class="col q-pa-md"
          v-if="request.category.type == 'experiment'"
        >
          <q-card>
            <q-card-section class="q-pa-sm bg-primary text-white">
              <div class="tw-text-center tw-text-2xl">
                 {{ request.category.type.charAt(0).toUpperCase() + request.category.type.slice(1) }} Information
              </div>
            </q-card-section>
            <q-separator/>
            <q-markup-table
              dense
            >
              <tbody>
                <tr>
                  <td class="tw-text-left">name</td>
                  <td class="tw-text-right">{{ request.category.category.name }}</td>
                </tr>
                <tr>
                  <td class="tw-text-left">os</td>
                  <td class="tw-text-right">
                    {{ request.category.category.os_info.distribution }} {{ request.category.category.os_info.version }}
                    <OsIcon size="2.5em" :item="request.category.category.os_info.os"/>
                  </td>
                </tr>
                <tr>
                  <td class="tw-text-left">description</td>
                  <td class="tw-text-right">{{ request.category.category.description }}</td>
                </tr>
                <tr>
                  <td class="tw-text-left">tests</td>
                  <td class="tw-text-right">
                    <div v-for="test in request.category.category.abstract_tests" :key="test.uuid">
                      <div class="row">
                        <div class="col">
                          {{ test.name }}
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td class="tw-text-left">run count</td>
                  <td class="tw-text-right">
                    <div class="col">
                      <div class="row justify-end">
                        <span class="tw-self-center">succesful</span>
                        <q-badge color="positive" class="q-ma-sm">
                          {{ request.category.category.run_counts.successful }}
                        </q-badge>
                      </div>
                      <div class="row justify-end">
                        <span class="tw-self-center">failed</span>
                        <q-badge color="negative" class="q-ma-sm">
                          {{ request.category.category.run_counts.failed }}
                        </q-badge>
                      </div>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td class="tw-text-left">more details</td>
                  <td class="tw-text-right">
                    <q-icon
                      name="add_circle"
                      color="secondary"
                      size="3em"
                      @click="NavigateToCategory()"
                    />
                  </td>
                </tr>
              </tbody>
            </q-markup-table>
          </q-card>
        </div>
        <div
          class="col q-pa-md"
          v-if="request.category.type == 'scenario'"
        >
          <q-card>
            <q-card-section class="q-pa-sm bg-primary text-white">
              <div class="tw-text-center tw-text-2xl">
                 {{ request.category.type.charAt(0).toUpperCase() + request.category.type.slice(1) }} Information
              </div>
            </q-card-section>
            <q-separator/>
            <q-markup-table
              dense
            >
              <tbody>
                <tr>
                  <td class="tw-text-left">name</td>
                  <td class="tw-text-right">{{ request.category.category.name }}</td>
                </tr>
                <tr>
                  <td class="tw-text-left">description</td>
                  <td class="tw-text-right">{{ request.category.category.description }}</td>
                </tr>
                <tr>
                  <td class="tw-text-left">tags</td>
                  <td class="tw-text-right">
                    <div class="flex tw-flex-wrap tw-max-w-sm tw-justify-end q-ml-auto">
                      <div v-for="tag in request.category.category.tags" :key="tag">
                        <q-badge color="primary" class="q-ml-md q-my-xs">
                          {{ tag }}
                        </q-badge>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </q-markup-table>
          </q-card>
        </div>
        <div
          class="col-2 q-pa-md"
          v-if="LoggedInUserStore.IsSupervisor"
        >
          <q-card>
            <q-card-section class="q-pa-sm bg-primary text-white">
              <div class="tw-text-center tw-text-2xl">
                 Actions
              </div>
            </q-card-section>
            <q-separator/>
            <q-markup-table
              dense
            >
              <tbody>
                <tr>
                  <td class="tw-text-left">Accept</td>
                  <td class="tw-text-right">
                    <q-icon
                      name="check_circle"
                      color="positive"
                      size="3em"
                      @click="accept_dialog = true"
                    />
                  </td>
                </tr>
                <tr>
                  <td class="tw-text-left">Reject</td>
                  <td class="tw-text-right">
                    <q-icon
                      name="cancel"
                      color="negative"
                      size="3em"
                      @click="reject_dialog = true"
                    />
                  </td>
                </tr>
                <tr>
                  <td class="tw-text-left">Assign</td>
                  <td class="tw-text-right">
                    <q-icon
                      name="assignment_ind"
                      color="secondary"
                      size="3em"
                      @click="assign_dialog = true"
                    />
                  </td>
                </tr>
                <tr
                  v-if="LoggedInUserStore.username == request.requestor"
                >
                  <td class="tw-text-left">Delete</td>
                  <td class="tw-text-right">
                    <q-icon
                      name="delete"
                      color="secondary"
                      size="3em"
                      @click="delete_dialog = true"
                    />
                  </td>
                </tr>
              </tbody>
            </q-markup-table>
          </q-card>
        </div>
      </q-card-section>
    </q-card>
  </div>

  <q-dialog
    v-model="accept_dialog"
  >
    <q-card>
        <q-toolbar>
          <q-toolbar-title>Accept Request</q-toolbar-title>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-toolbar>

        <q-card-section>
          <div class="text-h6">Are you sure you want to accept this request?</div>
          <br>
          <q-btn-group spread>
            <q-btn label="yes" @click="AcceptRequest()" v-close-popup class="bg-positive"/>
            <q-btn label="no" v-close-popup class="tw-bg-slate-200"/>
          </q-btn-group>
        </q-card-section>
      </q-card>
  </q-dialog>

  <q-dialog
    v-model="reject_dialog"
  >
    <q-card>
        <q-toolbar>
          <q-toolbar-title>Reject Request</q-toolbar-title>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-toolbar>

        <q-card-section>
          <div class="text-h6">Are you sure you want to reject this request?</div>
          <br>
          <q-btn-group spread>
            <q-btn label="yes" @click="RejectRequest()" v-close-popup class="bg-negative"/>
            <q-btn label="no" v-close-popup class="tw-bg-slate-200"/>
          </q-btn-group>
        </q-card-section>
      </q-card>
  </q-dialog>

  <q-dialog
    v-model="assign_dialog"
  >
    <q-card>
      <q-toolbar>
        <q-toolbar-title>Assign Request</q-toolbar-title>
        <q-btn flat round dense icon="close" v-close-popup />
      </q-toolbar>

      <q-card-section>
        <div class="text-h6">Choose the supervisor to assign to this request:</div>
        <br>
        <q-select
          v-model="selected_supervisor"
          :options="supervisors"
          option-label="username"
          option-value="username"
          emit-value
          map-options
          use-input
          fill-input
          hide-selected
          hide-dropdown-icon
          input-debounce="0"
          class="tw-bg-slate-200"
        >
          <template v-slot:option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section>
                <ProfileImage
                  :username="scope.opt"
                  tooltip="true"
                  linktoprofile="true"
                  size="sm"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ scope.opt }}</q-item-label>
              </q-item-section>
            </q-item>
          </template>
        </q-select>
        <br>
        <q-btn-group spread>
          <q-btn label="submit" v-close-popup class="tw-bg-slate-200" @click="AssignRequest()"/>
        </q-btn-group>
      </q-card-section>
    </q-card>
  </q-dialog>

  <q-dialog
    v-model="delete_dialog"
  >
    <q-card>
        <q-toolbar>
          <q-toolbar-title>Delete Request</q-toolbar-title>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-toolbar>

        <q-card-section>
          <div class="text-h6">Are you sure you want to delete this request?</div>
          <br>
          <q-btn-group spread>
            <q-btn label="yes" @click="DeleteRequest()" v-close-popup class="bg-negative"/>
            <q-btn label="no" v-close-popup class="tw-bg-slate-200"/>
          </q-btn-group>
        </q-card-section>
      </q-card>
  </q-dialog>

</template>


<script lang="ts">
import {onMounted, ref} from 'vue'
import { Request } from 'src/datatypes/scenario'
import axios from 'axios';
import RequestItemIcon from 'components/global/RequestItemIcon.vue';
import ProfileImage from 'components/ProfileImage.vue';
import StatusIcon from 'components/global/StatusIcon.vue';
import {status_color_mapping} from 'src/constants/mappings';
import { useRouter } from 'vue-router';
import { useLoggedInUserStore } from 'src/stores/loggedinuser';
import { storeToRefs } from 'pinia';
import OsIcon from 'components/global/OsIcon.vue';


export default {
  name: 'RequestOverview',

  components: {OsIcon, ProfileImage, StatusIcon, RequestItemIcon},

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

    const accept_dialog = ref<boolean>(false)
    const reject_dialog = ref<boolean>(false)
    const assign_dialog = ref<boolean>(false)
    const delete_dialog = ref<boolean>(false)

    const request = ref<Request | null>(null)
    const status_color = ref<string>('')

    const supervisors = ref<string[]>([])
    const selected_supervisor = ref<string>('')

    async function LoadRequest() {
      await axios.get('http://localhost:8000/api/request/'+props.uuid+'/').then(
        (response) => {
          request.value = response.data
        }
      )
    }

    async function LoadSupervisors() {
      await axios.get('http://localhost:8000/api/user/supervisors/names/').then(
        (response) => {
          supervisors.value = response.data
        }
      )
    }

    function NavigateToCategory() {
      if (request.value){
        router.push('/'+ request.value.category.type + '/'+request.value.category.category.uuid)
      }
    }

    async function AcceptRequest() {
      if (request.value){
        await axios.put('http://localhost:8000/api/request/'+props.uuid+'/accept/')
      }
      await LoadRequest()
    }

    async function RejectRequest() {
      if (request.value){
        await axios.put('http://localhost:8000/api/request/'+props.uuid+'/reject/')
      }
      await LoadRequest()
    }

    async function AssignRequest() {
      if (request.value){
        await axios.put('http://localhost:8000/api/request/'+props.uuid+'/assign/'+selected_supervisor.value+'/')
      }
      await LoadRequest()
    }

    async function DeleteRequest(){
      if (request.value){
        let resp = await axios.delete('http://localhost:8000/api/request/'+props.uuid+'/cancel/')
        if (resp.status == 403){
          console.log('not allowed to delete this request')
          return
        }
        if (resp.status == 200){
          await router.push('/requests')
        }
      }
      await LoadRequest()
    }

    onMounted(async () => {
      await LoadRequest()
      await LoadSupervisors()
      if (request.value) {
        status_color.value = 'bg-' + status_color_mapping[request.value.status.name as keyof typeof status_color_mapping]
      }
    })

    return {
      request,
      status_color,
      NavigateToCategory,
      AcceptRequest,
      RejectRequest,
      AssignRequest,
      DeleteRequest,
      LoggedInUserStore,
      accept_dialog,
      reject_dialog,
      assign_dialog,
      delete_dialog,
      supervisors,
      selected_supervisor,
    }
  }
}

</script>

