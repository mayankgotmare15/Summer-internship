package com.routedesk.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class AllowedAction(val actionCode: String) {
    @SerialName("update_status")
    UPDATE_STATUS("update_status"),

    @SerialName("change_eta")
    CHANGE_ETA("change_eta"),

    @SerialName("request_info")
    REQUEST_INFO("request_info"),

    @SerialName("hand_back")
    HAND_BACK("hand_back"),

    @SerialName("reassign")
    REASSIGN("reassign"),

    @SerialName("escalate")
    ESCALATE("escalate"),

    @SerialName("approve")
    APPROVE("approve"),

    @SerialName("reject")
    REJECT("reject"),

    @SerialName("confirm")
    CONFIRM_RESOLUTION("confirm"),

    @SerialName("reopen")
    REOPEN("reopen");

    companion object {
        fun fromCode(code: String): AllowedAction? =
            entries.firstOrNull { it.actionCode.equals(code, ignoreCase = true) }
    }
}
